import random
import time
import json
import os
import pkgutil
import re
from functools import partial
from enmutils.lib import log, filesystem
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError, JobValidationError, EnvironError
from enmutils.lib.headers import ASU_STATUS_FLOW_HEADER, JSON_SECURITY_REQUEST
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.load_mgr import get_active_profile_names
from enmutils_int.lib.nhm_widget import NhmWidget
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.nhc import create_nhc_profile, get_radio_node_package, NHC_PROFILE_DELETE_URL
from enmutils_int.lib.nhm import SETUP_PROFILE
from enmutils_int.lib.shm_utilities import SoftwarePackage
from enmutils_int.lib.shm_software_ops import SoftwareOperations
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Npa01Flow(GenericFlow):

    NPA_JSON_FILE_NAME = "npa_flow_input.json"
    NPA_FLOW_CREATE_URL = "/flowautomation/v1/flows/com.ericsson.oss.fa.flows.npa/execute"
    NPA_FLOW_STATUS_URL = "/flowautomation/v1/executions"
    NPA_FLOW_STOP_URL = "/flowautomation/v1/executions/{0}/stop"
    NHM_KPI_ACTIVATE = "kpi-specification-rest-api-war/kpi/active/True"
    NHM_KPI_DEACTIVATE = "kpi-specification-rest-api-war/kpi/active/False"
    KPIS_DEACTIVATE = None
    TOTAL_NODES = 0

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        node_ids_and_cells = []
        try:
            node_ids_and_cells = self.node_allocation_and_load_balance_as_a_prerequisite(user)
            profile_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
            health_check_profile_name = self.create_asu_health_check_profile(user, profile_nodes)
        except Exception as e:
            self.add_error_as_exception(e)
        while self.keep_running():
            try:
                if not node_ids_and_cells:
                    raise EnvironError("Couldn't allocate the synced nodes with required cells to create the flows")
                if not user.is_session_established():
                    raise EnmApplicationError("User is unable to login to ENM, please check the profile log for more details")
                self.create_and_execute_threads(node_ids_and_cells, self.NUMBER_OF_FLOWS,
                                                args=[user, health_check_profile_name, self])
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    def node_allocation_and_load_balance_as_a_prerequisite(self, user):
        """
        Get list of Radionodes allocated to NHM_SETUP profile and balance NHM KPI Load
        :param user: ENM user who will perform the query
        :type user: enm_user_2.Use
        :return: list of tuple of flow number and distributed node_ids_with cells per each flow
        :rtype: list
        """
        log.logger.debug("Allocating all synced RadioNodes from NHM_SETUP to NPA_01")
        synced_nodes_list = self.get_synced_nodes_from_setup_profile(user, SETUP_PROFILE, "RadioNode")
        radio_nodes_with_required_version, remaining_nodes = self.allocate_radionodes_from_synced_nodes(synced_nodes_list)
        list_of_node_ids, list_of_cells_name = self.get_names_of_nodes_and_cells(user, radio_nodes_with_required_version,
                                                                                 remaining_nodes, self.NUMBER_OF_CELLS)
        log.logger.debug("Total number of nodes chosen are: {0} and total number of cells chosen are: {1}".
                         format(len(set(list_of_node_ids)), len(list_of_cells_name)))
        profile_nodes = [profile_node for profile_node in synced_nodes_list if
                         profile_node.node_id in list(set(list_of_node_ids))]
        self.TOTAL_NODES = len(profile_nodes)
        self.deallocate_unused_nodes_and_update_profile_persistence(profile_nodes)
        log.logger.debug("Balancing NPA_01 load with NHM_SETUP initially by deactivating KPI's from NHM_SETUP ")
        self.balance_npa_load_with_nhm_setup(user)
        list_of_dict_of_node_ids_with_cells = self.group_cells_per_each_flow(list_of_node_ids,
                                                                             list_of_cells_name)
        return list_of_dict_of_node_ids_with_cells

    def allocate_radionodes_from_synced_nodes(self, synced_nodes_list):
        """
        Get list of synced RadioNodes allocated to the NHM_SETUP profile
        :param synced_nodes_list: List of synced node objects allocated from setup profile
        :type synced_nodes_list: list
        :return: tuple of Node objects allocated to this profile
        :rtype: tuple
        """
        radio_nodes_with_required_version, remaining_nodes = [], []
        radio_nodes_with_required_version = [node for node in synced_nodes_list if node.node_version in self.NODE_VERSION_FORMAT]
        log.logger.debug("The number of nodes available with the required version are:{}".format(len(radio_nodes_with_required_version)))
        remaining_nodes = [node for node in synced_nodes_list if node not in radio_nodes_with_required_version]
        return radio_nodes_with_required_version, remaining_nodes

    def get_synced_nodes_from_setup_profile(self, user, profile_name, node_type):
        """
        Get list of synced RadioNodes allocated to the NHM_SETUP profile
        :param user: ENM user who will perform the query
        :type user: enm_user_2.Use
        :param profile_name: The profile from which the nodes needs to be allocated
        :type profile_name: str
        :param node_type: Node type
        :type node_type: str
        :return: List of synced node objects allocated to this profile
        :rtype: list
        """
        setup_profile_nodes = self.get_allocated_nodes(profile_name)
        radio_nodes_in_setup_profile = [node for node in setup_profile_nodes if node.primary_type == node_type]
        self.allocate_specific_nodes_to_profile(radio_nodes_in_setup_profile)
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_ip", "netsim", "primary_type",
                                                                       "poid", "node_version"])
        log.logger.debug("Checking the sync status of the nodes and remove the nodes if not in sync")
        synced_nodes_list = check_sync_and_remove(nodes_list, user)[0]
        return synced_nodes_list

    def create_asu_health_check_profile(self, user, nodes):
        """
        Creates the Health Check Profile for the flows
        :param user: ENM user who will perform the query
        :type user: enm_user_2.User
        :param nodes: nodes to be used
        :type nodes: list
        :return: Health check profile created
        :rtype: str
        """
        health_check_profile_name = None
        software_package = SoftwarePackage(nodes, user, use_default=True, profile_name=self.NAME)
        radio_node_package = SoftwareOperations(user=user, package=software_package,
                                                ptype=nodes[0].primary_type)
        try:
            radio_node_package.import_package()
            radionode_package_dict = get_radio_node_package(user)
            health_check_profile_name = create_nhc_profile(user, nodes[0].primary_type, radionode_package_dict,
                                                           self.NAME)
            self.teardown_list.append(partial(picklable_boundmethod(self.delete_health_check_profile),
                                              user, health_check_profile_name))
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        return health_check_profile_name

    def select_node_and_cell_names(self, user, nodes, required_cell_count):
        """
        Get list of nodes of given type from nodes verified on ENM
        :param user: ENM user who will perform the query
        :type user: enm_user_2.User
        :param nodes: nodes to be used
        :type nodes: list
        :param required_cell_count: number of cells needed
        :type required_cell_count: int
        :return: list of node_ids and list of cells
        :rtype: tuple
        :raises EnvironError: when there are no available synced nodes
        """
        if not nodes:
            raise EnvironError("No available synced_nodes, cannot continue the flow execution")
        cells_names, nodes_names = [], []
        node_type = nodes[0].primary_type
        mo_names = ";".join(mo_name for mo_name in self.CELL_TYPE[node_type])
        node_ids_all = [node.node_id for node in nodes]
        node_id_chunks = chunks(node_ids_all, 30)
        for node_id_chunk in node_id_chunks:
            node_ids = ";".join(node_id for node_id in node_id_chunk)
            response = user.enm_execute('cmedit get {0} {1}'.format(node_ids, mo_names))
            if response:
                all_instances = [str(each_instance).split("ManagedElement=")[-1]
                                 for each_instance in response.get_output() if "ManagedElement" in each_instance]
                node_output = [each_instance.split(",")[0] for each_instance in all_instances]
                cell_output = [each_instance.split("=")[-1] for each_instance in all_instances]
                cell_count = len(cells_names) + len(cell_output)
                if cell_count <= required_cell_count:
                    nodes_names.extend(node_output)
                    cells_names.extend(cell_output)
                else:
                    remaining_cells = required_cell_count - len(cells_names)
                    nodes_names.extend(node_output[:remaining_cells])
                    cells_names.extend(cell_output[:remaining_cells])
                    break
        return nodes_names, cells_names

    def get_names_of_nodes_and_cells(self, user, radio_nodes_with_required_version, remaining_nodes,
                                     required_cell_count):
        """
        Get mixed list of nodes and cells if higher version nodes available
        :param user: ENM user who will perform the query
        :type user: enm_user_2.User
        :param radio_nodes_with_required_version: NHC supported nodes to be used
        :type radio_nodes_with_required_version: list
        :param remaining_nodes: Other supported nodes to be used for the flows
        :type remaining_nodes: list
        :param required_cell_count: number of cells needed
        :type required_cell_count: int
        :return: list of node_ids and list of cells
        :rtype: tuple
        """
        nodes_names, cells_names = [], []
        if radio_nodes_with_required_version:
            nodes_names, cells_names = self.select_node_and_cell_names(user, radio_nodes_with_required_version,
                                                                       required_cell_count)
            if len(cells_names) < required_cell_count:
                cells_still_required = required_cell_count - len(cells_names)
                nodes_names_other, cells_names_other = self.select_node_and_cell_names(user, remaining_nodes,
                                                                                       cells_still_required)
                nodes_names.extend(nodes_names_other)
                cells_names.extend(cells_names_other)
        else:
            nodes_names, cells_names = self.select_node_and_cell_names(user, remaining_nodes, required_cell_count)
        return nodes_names, cells_names

    def group_cells_per_each_flow(self, node_names, cells_names):
        """
        Generates list of node ids with cells for total flows passed in config file
        :param node_names: list of node_ids
        :type node_names: list
        :param cells_names: list of cells names
        :type cells_names: list
        :return: list of tuple of flow number and distributed node_ids_with cells per each flow
        :rtype: list
        """
        nodes_and_cells = zip(node_names, cells_names)
        dict_nodes_and_cells = {}
        for node, cell in nodes_and_cells:
            if not dict_nodes_and_cells.get(node):
                dict_nodes_and_cells[node] = [cell]
            else:
                dict_nodes_and_cells[node].append(cell)
        list_of_dict_nodes_and_cells_all_flows = self.limit_nodes_and_cells_per_each_flow(
            dict_nodes_and_cells, self.NUMBER_OF_FLOWS)
        distributed_nodes_and_cells = [(flow_number + 1, each_flow) for flow_number, each_flow in
                                       enumerate(list_of_dict_nodes_and_cells_all_flows)]
        return distributed_nodes_and_cells

    @staticmethod
    def limit_nodes_and_cells_per_each_flow(dict_nodes_and_cells, number_of_flows):
        """
        Generates the tuple of node ids with cells for each flow limiting to less than unique 50 nodes / 500 cells
        (npa flow constraint)
        :param dict_nodes_and_cells: dict of nodes and cells
        :type dict_nodes_and_cells: dict
        :param number_of_flows: number of npa flows to run concurrently
        :type number_of_flows: int
        :return: list of distributed node names and cells names per each flow
        :rtype: list
        """
        nodes_limit, cells_limit = 50, 500
        node_ids = dict_nodes_and_cells.keys()
        list_nodes_cells_all_flows = []
        for each_flow in range(number_of_flows):
            nodes_cells_per_flow = node_ids[each_flow::number_of_flows][:nodes_limit]
            dict_nodes_cells_per_flow = {each_node: dict_nodes_and_cells[each_node]
                                         for each_node in nodes_cells_per_flow}
            number_of_cells_per_flow = sum([len(each_node_cells) for each_node_cells in
                                            dict_nodes_cells_per_flow.values()])
            while number_of_cells_per_flow and number_of_cells_per_flow > cells_limit:
                dict_nodes_cells_per_flow.pop(dict_nodes_cells_per_flow.keys()[0])
                number_of_cells_per_flow = sum([len(each_node_cells) for each_node_cells in
                                                dict_nodes_cells_per_flow.values()])
            list_nodes_cells_all_flows.append(dict_nodes_cells_per_flow)
        return list_nodes_cells_all_flows

    def balance_npa_load_with_nhm_setup(self, user):
        """
        :type user: `enm_user_2.User`
        :param user: ENM user used to activate/deactivate kpis
        """
        active_profiles = get_active_profile_names()
        if SETUP_PROFILE in active_profiles or "NHM_01_02" in active_profiles:
            self.reduce_nhm_kpi_load(user)
            self.teardown_list.append(partial(picklable_boundmethod(self.reactivate_nhm_kpi_load), user))
        else:
            log.logger.debug("NHM_SETUP or NHM_01_02 profile is not running, continuing NPA_01 flow")

    def reduce_nhm_kpi_load(self, user):
        """
        Reduce the kpis which already created for nhm_setup or nhm_01_02 profile as per config file before starting
        npa_01 if nhm_setup or nhm_01_02 profile was already running
        For 60k/40k deployment, the load considered to reduce is 8k
        For 15k deployment, the load considered to reduce is 3.2k
        For 5k/1k deployment, the load considered to reduce is 1.6k
        :param user: ENM user object used to perform put request for deactivating kpis
        :type user: enm_user_2.User
        :raises EnmApplicationError: when kpis deactivation fails
        """
        nhm_widget = NhmWidget(user, nodes=None)
        list_of_available_kpis = nhm_widget._get_available_kpis()
        list_of_kpi_names = [kpi_name.get("kpiName") for kpi_name in list_of_available_kpis if kpi_name.get("active")]
        list_of_nhm_kpis = [nhm_kpi for nhm_kpi in list_of_kpi_names
                            if SETUP_PROFILE in nhm_kpi or "NHM_01_02" in nhm_kpi]
        self.KPIS_DEACTIVATE = (random.sample(list_of_nhm_kpis, self.KPI_ADJUST)
                                if self.KPI_ADJUST <= len(list_of_nhm_kpis) else list_of_nhm_kpis)
        log.logger.debug("list of chosen kpi_names to deactivate are: {0}".format(self.KPIS_DEACTIVATE))
        response = user.put(url=self.NHM_KPI_DEACTIVATE, data=json.dumps(self.KPIS_DEACTIVATE),
                            headers=JSON_SECURITY_REQUEST)
        if response.ok:
            log.logger.debug("Kpis deactivation was Success")
        else:
            raise EnmApplicationError("Unable to deactivate the NHM kpis")

    def reactivate_nhm_kpi_load(self, user):
        """
        Reactivate the for nhm_setup or nhm_01_02 profile as per config file in case if npa_01 stopped and nhm_01_02 or
        nhm_setup running
        For 60k/40k deployment, the load considered to recreate is 8k
        For 15k deployment, the load considered to recreate is 3.2k
        For 5k/1k deployment, the load considered to recreate is 1.6k
        :param user: ENM user object used to perform put request for activating kpis
        :type user: enm_user_2.User
        :raises EnmApplicationError: when kpis reactivation fails
        """
        active_profiles = get_active_profile_names()
        if self.KPIS_DEACTIVATE and (SETUP_PROFILE in active_profiles or "NHM_01_02" in active_profiles):
            log.logger.debug("list of chosen kpi_names to reactivate are: {0}".format(self.KPIS_DEACTIVATE))
            response = user.put(url=self.NHM_KPI_ACTIVATE, data=json.dumps(self.KPIS_DEACTIVATE),
                                headers=JSON_SECURITY_REQUEST)
            if response.ok:
                log.logger.debug("Kpis re-activation was Success")
            else:
                raise EnmApplicationError("Unable to reactivate the NHM kpis")

    @staticmethod
    def task_set(node_ids_with_cells_flow_instance, user, health_check_profile_name, profile):  # pylint: disable=arguments-differ
        """
        :type node_ids_with_cells_flow_instance: tuple
        :param node_ids_with_cells_flow_instance: tuple of flow instance number, dict of node ids with cells names
        :type user: `enm_user_2.User`
        :param user: ENM user used to create npa flow and activate kpis, status check and stop the flow
        :param health_check_profile_name: Name of the Health Check Profile
        :type health_check_profile_name: str
        :type profile: `lib.profile.Profile`
        :param profile: profile object used for function calls
        :raises JobValidationError: when flow unable to start/initialize
        :raises EnmApplicationError: when flow goes to unexpected state
        :raises HttpError: when response is not correct
        """
        try:
            log.logger.debug("Starting NPA_01 flow creation process....")
            flow_instance, node_ids_with_cells = node_ids_with_cells_flow_instance
            flow_name = re.sub('[^A-Za-z0-9]+', '',
                               "{0}Time{1}Flow{2}".format(profile.NAME,
                                                          profile.get_timestamp_str(timestamp_end_index=8),
                                                          flow_instance))
            log.logger.debug("Current_flow: {0} nodes dict is: {1}".format(flow_name, node_ids_with_cells))
            npa01_folder = "/home/enmutils/npa_01/{0}".format(flow_name)
            profile.create_directory_for_npa_flow(npa01_folder)
            npa01_json_file_path = "{0}/{1}".format(npa01_folder, profile.NPA_JSON_FILE_NAME)
            profile.prepare_json_file_for_npa_flow(node_ids_with_cells, health_check_profile_name, npa01_json_file_path)
            profile.create_npa_flow(user, flow_name, npa01_json_file_path)
            log.logger.debug("Sleeping for 60 secs after NPA01_FLOW_Creation")
            time.sleep(60)
            profile.verify_flow_status(user, flow_name)
        except Exception as e:
            profile.add_error_as_exception(EnmApplicationError("Failed to run NPA flow, Exception: [{0}]"
                                                               .format(e.message)))

    def create_directory_for_npa_flow(self, npa01_folder):
        """
        Creates directory structure based on flow name to copy json file, edit json file contents
        :type npa01_folder: str
        :param npa01_folder: npa flow name
        """
        if not filesystem.does_dir_exist(npa01_folder):
            filesystem.create_dir(npa01_folder)
        self.teardown_list.append(partial(picklable_boundmethod(self.delete_directory_for_npa_flow), npa01_folder))

    def delete_directory_for_npa_flow(self, npa01_folder):
        """
        Deletes the created npa flow directory in teardown
        :type npa01_folder: str
        :param npa01_folder: npa flow name
        """
        filesystem.remove_dir(npa01_folder)

    def delete_health_check_profile(self, user, health_check_profile_name):
        """
        Deletes the Health Check Profile
        :param user: ENM user who will perform the query
        :type user: enm_user_2.User
        :param health_check_profile_name: Health Check Profile to be deleted
        :type health_check_profile_name: str
        """
        log.logger.debug("Attempting to delete the Health Check Profile:{0}".format(health_check_profile_name))
        try:
            user.post(NHC_PROFILE_DELETE_URL, json=[health_check_profile_name], headers=JSON_SECURITY_REQUEST)
        except Exception as e:
            log.logger.debug("Failed to delete the profile {0}: {1}".format(health_check_profile_name, str(e)))
        else:
            log.logger.debug("Health Check Profile:{0} has been successfully deleted".format(health_check_profile_name))

    def prepare_json_file_for_npa_flow(self, node_ids_with_cells, health_check_profile_name, npa01_json_file_path):
        """
        Prepare the json file with node and cell names data and create the file in respective directory
        :type node_ids_with_cells: dict
        :param node_ids_with_cells: dict of node ids with their cells names
        :param health_check_profile_name: Name of the Health Check Profile
        :type health_check_profile_name: str
        :type npa01_json_file_path: str
        :param npa01_json_file_path: path of json file to be created
        """
        node_ids = ",".join(node_ids_with_cells.keys())
        cells_names = [cell_name for node_id in node_ids_with_cells.values() for cell_name in node_id]
        internal_package_path = pkgutil.get_loader("enmutils_int").filename
        npa01_template_path = os.path.join(internal_package_path, "templates", "asu", self.NPA_JSON_FILE_NAME)
        with open(npa01_template_path) as fd:
            flow_input = json.load(fd)
        flow_input["rawNumberOfCells"] = len(cells_names)
        flow_input["rawNodeCells"] = node_ids_with_cells
        flow_input["rawNetworkElements"] = [node_ids]
        flow_input["networkElementConfiguration"]["neNames"] = node_ids
        if health_check_profile_name:
            flow_input["activities"]["nhcActivity"]["selectedHealthCheckProfiles"][0]["name"] = health_check_profile_name
        with open(npa01_json_file_path, "w+") as json_file:
            json.dump(flow_input, json_file, indent=4)
            json_file.seek(0)
            log.logger.debug("NPA_01 profile user input json file content is:\n{0}".format(json_file.read()))

    def create_npa_flow(self, user, flow_name, npa01_json_file_path):
        """
        Creates Network Performance Acceptance flow with provided json file input via rest call
        :type user: `enm_user_2.User`
        :param user: ENM user used to create npa flow and activate kpis
        :type flow_name: str
        :param flow_name: name of the npa flow
        :type npa01_json_file_path: str
        :param npa01_json_file_path: path of json file
        :raises HttpError: when response is not correct
        """
        files = {'name': (None, flow_name), 'file-name': (None, self.NPA_JSON_FILE_NAME),
                 'flow-input': open(npa01_json_file_path, 'rb')}
        log.logger.debug("Attempting to create NPA_01 new flow with name {0}".format(flow_name))
        response_create = user.post(self.NPA_FLOW_CREATE_URL, data={}, files=files, headers=ASU_STATUS_FLOW_HEADER)
        if response_create.status_code != 200:
            log.logger.debug("NPA_01_Flow_Creation response_status_code is: {0} \n"
                             "response_request_header is: {1} \nresponse_request_body is: {2}"
                             .format(response_create.status_code, response_create.request.headers,
                                     response_create.request.body))
            raise_for_status(response_create,
                             message_prefix="Failed to create new flow with id {0}".format(flow_name))
        else:
            self.teardown_list.append(partial(picklable_boundmethod(self.stop_npa_flow_in_ui), user, flow_name))
            log.logger.debug("Completed creating NPA_01 new flow with name {0}".format(flow_name))

    def verify_flow_status(self, user, flow_name):
        """
        Verifies the npa flow status after flow creation via rest call
        :type user: `enm_user_2.User`
        :param user: ENM user used to stop npa flow
        :type flow_name: str
        :param flow_name: name of the npa flow
        :raises EnmApplicationError: when flow goes to unexpected or failed or in setup state
        """
        flow_state = self.get_current_state_of_npa_flow(user, flow_name)
        if flow_state and flow_state.lower() == "executing":
            log.logger.debug("NPA Flow: {0} was successfully collecting kpis".format(flow_name))
        elif flow_state and "fail" in flow_state.lower():
            raise EnmApplicationError("NPA Flow: {0} was failed with flow state: {1}".format(flow_name, flow_state))
        elif flow_state and "setup" in flow_state.lower():
            log.logger.debug("NPA Flow: {0} was still in setup phase".format(flow_name))
        else:
            log.logger.debug("NPA Flow: {0} was not in expected state".format(flow_name))
        log.logger.debug("Sleeping for 5 minutes and thereafter will verify the flow: {0} status again"
                         .format(flow_name))
        time.sleep(300)
        flow_state_after = self.get_current_state_of_npa_flow(user, flow_name)
        if flow_state_after and flow_state_after.lower() == "executing" or flow_state_after.lower() == "executed":
            log.logger.debug("Completed NPA Flow: {0} check and it is running fine!".format(flow_name))
        elif flow_state_after and flow_state_after.lower() == "execute":
            raise EnmApplicationError("NPA Flow: {0} was not initialized".format(flow_name))
        else:
            raise EnmApplicationError("NPA Flow: {0} state was not in expected state".format(flow_name))

    def stop_npa_flow_in_ui(self, user, flow_name):
        """
        Forcefully stops the npa flow via rest call
        :type user: `enm_user_2.User`
        :param user: ENM user used to stop npa flow
        :type flow_name: str
        :param flow_name: name of the npa flow
        """
        flow_state = self.get_current_state_of_npa_flow(user, flow_name)
        if flow_state and "setup" in flow_state.lower() and "fail" not in flow_state.lower():
            log.logger.debug("NPA flow: {0} state is in {1} and cannot be stopped forcefully. "
                             "Note: Also there is a chance that flow resumes its execution at later point of time"
                             .format(flow_name, flow_state))
        else:
            params_stop = (('flow-id', 'com.ericsson.oss.fa.flows.npa'),)
            resp = user.put(self.NPA_FLOW_STOP_URL.format(flow_name), params=params_stop)
            if resp.ok:
                log.logger.debug("NPA flow: {0} stop Completed".format(flow_name))
            else:
                log.logger.debug("NPA flow: {0} stop Failed".format(flow_name))

    def get_current_state_of_npa_flow(self, user, flow_name):
        """
        Fetch the current status of npa flow via rest call
        :type user: `enm_user_2.User`
        :param user: ENM user used to get status of npa flow
        :type flow_name: str
        :param flow_name: name of the npa flow
        :raises JobValidationError: when flow unable to start/initialize
        :return: npa flow current state
        :rtype: str
        """
        params_status = (('flow-id', 'com.ericsson.oss.fa.flows.npa'),
                         ('flow-execution-name', '{0}'.format(flow_name)))
        response = user.get(self.NPA_FLOW_STATUS_URL, params=params_status)
        if not response.ok:
            raise JobValidationError("Cannot get flow status, status was {0}"
                                     " text was {1}".format(response.status_code, response.text), response=response)
        else:
            json_response = response.json()
            flow_state = json_response[0].get("state")
            flow_sum_rep = json_response[0].get("summaryReport")
            log.logger.debug("NPA_01 NPA Flow: {0} current state is: {1} and summary report is: {2}"
                             .format(flow_name, flow_state, flow_sum_rep))
            return flow_state
