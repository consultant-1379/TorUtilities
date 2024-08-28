import random
import re
import time
import copy
from math import ceil
from functools import partial
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib import log, cache
from enmutils.lib.exceptions import EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError
from enmutils.lib.shell import Command, run_cmd_on_vm, run_remote_cmd, run_local_cmd
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.profile_flows.cbrs_flows.cbrs_cpi import CbrsCpi, cbrscpi_teardown
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_list_of_scripting_service_ips
from enmutils_int.lib.services.deployment_info_helper_methods import get_cloud_native_service_ips
from retrying import retry

GET_CBRS_ENABLED_CELLS = 'cmedit get * EUtranCellTDD.cbrscell==true'
GET_CBRS_NR_ENABLED_CELLS = 'cmedit get * NRSectorCarrier.cbrsEnabled==true'
CREATE_MAINTENANCE_USER_MO_LTE = 'cmedit create SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,' \
                                 'ManagedElement={0},SystemFunctions=1,SecM=1,UserManagement=1,UserIdentity=1,' \
                                 'MaintenanceUser=1 maintenanceUserId=1;subjectName="CN=MaintenanceUser"'
CREATE_MAINTENANCE_USER_MO_NR = 'cmedit create SubNetwork=Europe,SubNetwork=Ireland,MeContext={0},' \
                                'ManagedElement={0},SystemFunctions=1,SecM=1,UserManagement=1,UserIdentity=1,' \
                                'MaintenanceUser=1 maintenanceUserId=1;subjectName="CN=MaintenanceUser"'
BASE_ADD_CMD = 'cbrs add "{0}{1}:{2}"'
NR_BASE_ADD_CMD = 'cbrs add "{0}{1}:{2}:{3}"'
PRODUCT_NUMBER_CMD = "cmedit get * FieldReplaceableUnit.(positionCoordinates,productData) -ne=RadioNode"
RF_BRANCH_REF = "cmedit get * SectorEquipmentFunction.rfBranchRef"
SAS_MANUAL_SETUP_PAGE = ('https://eteamspace.internal.ericsson.com/display/TORRV/Manual+SAS+and+Domain+Proxy+setup+in+Release')

SET_CHANNEL_MASK = 'cbrs set --channelmask {0} "{1}{2}"'
SET_MIXPAL_CHANNEL_MASK = 'cbrs set --mixpalchannelmask {0} "{1}{2}"'
SET_MIXPALGAA = 'cbrs set --mixpalgaa {0} "{1}{2}"'

UNMAP_NODES_TO_SA_DC = 'cbrs set --cbrsfunction default {0}'
MAP_NODES_TO_SA_DC = 'cbrs set --cbrsfunction {0} {1}'
SET_SAS_URL = 'cbrs config --sas-url {0}'
SET_SA_DC_AND_SAS_URL = 'cbrs config --cbrsfunction {0} --sas-url {1}'
LTE_MAPPING_SUBNETWORK = "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement={0}"
NR_MAPPING_SUBNETWORK = "SubNetwork=Europe,SubNetwork=Ireland,MeContext={0},ManagedElement={0}"

XML_FILE_NAME = 'trust_cert_file_{0}.xml'
XML_CERT_DIR = '/home/enmutils/cbrs/{0}'
TRUST_CERT_PRE = 'secadm certificate issue --certtype OAM --xmlfile file:{0}'

DEVICE_RADIODOT = "RadioDot"
DEVICE_2208 = "2208"
DEVICE_4408 = "4408"
DEVICE_6488 = "6488"
DEVICE_NR_4408 = "NR_4408"
DEVICE_PASSIVE_DAS_4408 = "PassiveDas_4408"
PRODUCT_ID_DICT = {DEVICE_6488: "KRD 901 160/11", DEVICE_4408: "KRC 161 746/1", DEVICE_2208: "KRC 161 711/1",
                   DEVICE_RADIODOT: "KRY 901 385/1", DEVICE_NR_4408: "KRC 161 746/1"}
CHUNK_SIZE = 300
CERT_POLL_COUNT = 16
CERT_POLL_TIMER = 100


class CbrsSetupFlow(GenericFlow):

    def __init__(self, *args, **kwargs):
        super(CbrsSetupFlow, self).__init__(*args, **kwargs)
        self.scripting_vms_with_ports = None
        self.scripting_vms_without_ports = None
        self.cbrs_cell_fdns = []
        self.add_group_commands = []
        self.cell_grouping_for_pal_policies = []
        self.nodes_selected_by_device_type = {}
        self.used_nodes = []
        self.node_ids = []
        self.product_data_split = []
        self.sorted_cbrs_cells = {}
        self.fru_dict = {}
        self.product_data_dict = {}
        self.rf_branch_count_dict = {}
        self.rf_data_dict = {}
        self.cell_size = {2: [], 3: [], 6: [], 12: []}
        self.device_type = {DEVICE_RADIODOT: [], DEVICE_2208: [], DEVICE_4408: [], DEVICE_6488: [], DEVICE_NR_4408: [],
                            DEVICE_PASSIVE_DAS_4408: []}
        self.device_count_dict_by_device_type = {DEVICE_2208: 0, DEVICE_RADIODOT: 0, DEVICE_4408: 0, DEVICE_6488: 0,
                                                 DEVICE_NR_4408: 0, DEVICE_PASSIVE_DAS_4408: 0}
        self.groups_for_each_device_type = copy.deepcopy(self.device_type)
        self.groups_available_for_pal = copy.deepcopy(self.device_count_dict_by_device_type)
        self.groups_wanted_for_pal_policies = copy.deepcopy(self.device_count_dict_by_device_type)
        self.groups_wanted_for_mixpalgaa = copy.deepcopy(self.device_count_dict_by_device_type)
        self.pal_4408_groups_used = []
        self.pal_6488_groups_used = []
        self.lists_pal_groups_used = [self.pal_4408_groups_used, self.pal_6488_groups_used]
        self.mixpalgaa_6488_groups_used = []
        self.mixpalgaa_4408_groups_used = []
        self.lists_mixpalgaa_groups_used = [self.mixpalgaa_4408_groups_used, self.mixpalgaa_6488_groups_used]
        self.lite_nodes = []
        self.passive_das_4408_nodes = []
        self.mapped_paths_for_nodes = []
        self.device_count_dict_per_node = {}
        self.product_data_per_node = {}
        self.is_on_cenm = False
        self.failed_maintenance_user_created_nodes = []
        self.start_range_for_batch = 0
        self.end_range_for_batch = 0
        self.batch_num_required = 0
        self.batch_node_count = 0
        self.trust_cert_xml_list = []
        self.failed_trust_cert_xmls = []

    def execute_flow(self):
        """
        Profile main flow.
        """
        user = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False)[0]
        self.state = "RUNNING"
        try:
            self.initial_startup(user)
        except (EnmApplicationError, EnvironError) as e:
            e.message = ("Profile's initial setup has failed: {0}. Ensure manual set up "
                         "steps have been completed {1}".format(SAS_MANUAL_SETUP_PAGE, e.message))
            self.add_error_as_exception(e)
            log.logger.debug("Due to failure the profile will now go to completed.")
            self.update_nodes_used_by_profile()
            return

        try:
            self.sort_select_cells_and_build_add_commands(user)
        except Exception as e:
            self.add_error_as_exception(e)
            log.logger.debug('Profile could not get cbrs cells. Profile will now go to completed.')
            self.update_nodes_used_by_profile()
            return
        self.cert_and_trust_distribution_on_nodes(user)
        self.create_maintenance_user_mo_on_node(user)
        self.map_nodes_to_standalone_domain_coordinator(user)
        self.set_standalone_domain_coordinator(user)
        self.set_pal_policies_for_cbrs_groups(user)
        self.execute_cbrs_add_commands(user)
        self.build_summary()
        # teardown is LIFO, groups get removed first.
        if self.is_on_cenm:
            self.teardown_list.append(partial(cbrscpi_teardown, self.scripting_vms_with_ports))
        else:
            self.teardown_list.append(partial(cbrscpi_teardown, self.scripting_vms_without_ports))
        self.teardown_list.append(partial(picklable_boundmethod(self.teardown_pal_policies), user))
        self.teardown_list.append(partial(picklable_boundmethod(self.cleanup_mapped_nodes_on_teardown), user))
        self.teardown_list.append(partial(picklable_boundmethod(self.remove_groups), user, self.scripting_vms_without_ports))
        self.teardown_list.append(partial(picklable_boundmethod(self.remove_trust_cert_xml_on_teardown)))

    def initial_startup(self, user):
        """
        Carry out initial start up checks.

        :param user: User with admin rights
        :type user: `enmutils.enm_user_2`
        """
        log.logger.debug('Fetching list of scripting ips')
        self.lite_nodes = self.get_nodes_list_by_attribute(node_attributes=['profiles', 'node_id'])
        if cache.is_enm_on_cloud_native():
            self.is_on_cenm = True
            deployment_namespace = cache.get_enm_cloud_native_namespace()
            log.logger.debug("Profile on cENM deployment")
            self.scripting_vms_with_ports, self.scripting_vms_without_ports = get_cloud_native_service_ips('general-scripting', deployment_namespace)
            cbrscpi_teardown(random.choice(self.scripting_vms_with_ports))
        else:
            self.scripting_vms_without_ports = get_list_of_scripting_service_ips()
            cbrscpi_teardown(random.choice(self.scripting_vms_without_ports))
            log.logger.debug('Checking if SAS is correctly configured.')
        log.logger.debug('Running cbrs remove command to ensure no groups left over from previous run')
        self.remove_groups(user, self.scripting_vms_without_ports)

    def sort_select_cells_and_build_add_commands(self, user):
        """
        Select the CBRS nodes, sort into device type and generate the add commands

        :param user: ENM user who will perform the query(ies)
        :type user: `enm_user_2.User`
        """
        self.get_cbrs_cells_via_cmedit(user)
        self.is_nr_cbrs_cells_required_for_iteration(user)
        self.sort_by_cell_size()
        self.get_all_product_data(user)
        self.build_product_data_dict()
        self.get_fru_count()
        self.get_rf_branch(user)
        self.sort_device_type()
        self.device_type[DEVICE_PASSIVE_DAS_4408] = self.device_type.get(DEVICE_4408)
        self.get_required_number_of_devices()
        self.device_type[DEVICE_PASSIVE_DAS_4408] = self.passive_das_4408_nodes
        self.generate_cbrs_add_commands()
        if self.is_on_cenm:
            CbrsCpi.execute_cpi_flow(CbrsCpi(), self.scripting_vms_with_ports, self.device_type, self.product_data_dict, self.used_nodes,
                                     self.rf_branch_count_dict, user)
        else:
            CbrsCpi.execute_cpi_flow(CbrsCpi(), self.scripting_vms_without_ports, self.device_type, self.product_data_dict,
                                     self.used_nodes,
                                     self.rf_branch_count_dict, user)

    def build_summary(self):
        """
        Builds a summary to show how many devices are expected / added and the number of groups to expect
        at the end of the profile
        """
        log.logger.debug("Devices expected by the profile : {0}".format(self.DEVICES_REQUIRED))
        log.logger.debug("Devices added by the profile : {0}".format(self.device_count_dict_by_device_type))
        log.logger.debug("Number of groups expected to be added by the profile: {0}".format(len(
            self.add_group_commands)))
        log.logger.debug("Number of nodes mapped to Standalone domain co-ordinator : {0}".format(len(
            self.mapped_paths_for_nodes)))
        log.logger.debug("Groups wanted for pal policies to be set : {0}".format(self.groups_wanted_for_pal_policies))
        log.logger.debug("Number of 4408 Groups set for pal policies: {0}".format(len(self.pal_4408_groups_used)))
        log.logger.debug("Number of 6488 Groups set for pal policies: {0}".format(len(self.pal_6488_groups_used)))
        log.logger.debug(
            "Groups wanted for mixpalgaa policies to be set : {0}".format(self.groups_wanted_for_mixpalgaa))
        log.logger.debug(
            "Number of Groups set for 4408 mixpalgaa policies: {0}".format(len(self.mixpalgaa_4408_groups_used)))
        log.logger.debug(
            "Number of Groups set for 6488 mixpalgaa policies: {0}".format(len(self.mixpalgaa_6488_groups_used)))
        log.logger.debug("Maintenance User MO failed to create on [{0}] Nodes they are: {1}".format(len(self.failed_maintenance_user_created_nodes), self.failed_maintenance_user_created_nodes))
        log.logger.debug("{0}: trust cert batches failed they are : {1}".format(len(self.failed_trust_cert_xmls), self.failed_trust_cert_xmls))

    @retry(retry_on_exception=lambda e: isinstance(e, (EnvironError, EnmApplicationError,
                                                       NoOuputFromScriptEngineResponseError)), wait_fixed=5000,
           stop_max_attempt_number=3)
    def get_cbrs_cells_via_cmedit(self, user):
        """
        Fetch all cbrs enabled cells using cmedit

        :param user: user object
        :type user: `enmutils.enm_user_2`

        :raises e: if any of the below is True
        :raises EnvironError: If no cbrs enabled cells present on deployment
        :raises NoOuputFromScriptEngineResponseError: If no response from ENM
        :raises EnmApplicationError: If there is an error such as a timeout while executing command
        """
        log.logger.debug("Querying deployment for CBRS enabled cells.")
        try:
            response = user.enm_execute(GET_CBRS_ENABLED_CELLS)
            output = response.get_output()
            if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in output):
                raise EnvironError('Could not find any cbrs enabled cells on deployment')
        except (EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError) as e:
            log.logger.debug('Could not fetch cells due to {0}'.format(e))
            raise e
        for fdn in output:
            if 'FDN' in fdn:
                self.cbrs_cell_fdns.append(fdn)
        log.logger.debug("Completed querying deployment for CBRS enabled cells.")

    def is_nr_cbrs_cells_required_for_iteration(self, user):
        """
        Checks the NR4408 value in Forty Network
        :param user: user object
        :type user: `enmutils.enm_user_2`
        :return:
        """
        log.logger.debug("Checking if NR cells are required for profile iteration")
        for device_type, num_required in self.DEVICES_REQUIRED.items():
            if "NR_4408" in device_type and num_required > 0:
                self.get_nr_cbrs_cells_via_cmedit(user)
            elif "NR_4408" in device_type and num_required == 0:
                log.logger.debug("Number of NR4408's required is 0 so cells for NR will not be requested")
        log.logger.debug("Finished the Check if NR cells are required for profile iteration")

    def get_nr_cbrs_cells_via_cmedit(self, user):
        """
        Fetch all nr cbrs enabled cells using cmedit

        :param user: user object
        :type user: `enmutils.enm_user_2`

        :raises e: if any of the below is True
        :raises EnvironError: If no nr cbrs enabled cells present on deployment
        :raises NoOuputFromScriptEngineResponseError: If no response from ENM
        :raises EnmApplicationError: If there is an error such as a timeout while executing command
        """
        log.logger.debug("Querying deployment for NR CBRS enabled cells.")
        try:
            response = user.enm_execute(GET_CBRS_NR_ENABLED_CELLS)
            output = response.get_output()
            if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in output):
                log.logger.debug("No NR cell available on ENM to be fetch")
        except (EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError) as e:
            log.logger.debug('Could not fetch cells due to {0}'.format(e))
            raise e
        for fdn in output:
            if 'FDN' in fdn:
                self.cbrs_cell_fdns.append(fdn)
        log.logger.debug("Completed querying deployment for NR CBRS enabled cells.")

    def sort_by_cell_size(self):
        """
        Sort the CBRS enabled cells by node id
        """
        log.logger.debug("Sorting CBRS enabled cells by Node id.")
        for fdn in self.cbrs_cell_fdns:
            fdn_node_id = re.findall('ManagedElement=(.*?),', fdn)[0]
            if fdn_node_id not in self.sorted_cbrs_cells.keys():
                self.sorted_cbrs_cells[fdn_node_id] = []
            self.sorted_cbrs_cells[fdn_node_id].append(fdn)
        self.sort_cells_numerical_order()
        for node_id, cells in self.sorted_cbrs_cells.items():
            if len(cells) not in self.cell_size.keys():
                log.logger.debug("{0} has {1} Cells which is not currently supported in the profile".format(node_id, len(cells)))
                self.sorted_cbrs_cells.pop(node_id)
            else:
                self.cell_size.get(len(cells)).append(node_id)
        log.logger.debug("Completed sort of CBRS enabled cells by Node id.")

    def sort_cells_numerical_order(self):
        """
        Sorts node cells Numerically for adding groups
        """
        sorted_cells_by_fdn = {}
        for k, v in self.sorted_cbrs_cells.items():
            if "gNodeBRadio" in k:
                for _ in v:
                    value_split = v[0].split("NRSectorCarrier=")[0]
                    cell_ids = sorted([int(cell_id.split("NRSectorCarrier=")[1]) for cell_id in v])
                    sorted_cells_by_fdn[k] = ["{0}NRSectorCarrier={1}".format(value_split, cell_no) for cell_no in
                                              cell_ids]
            else:
                value_split = v[0].split("-")[0]
                cell_ids = sorted([int(cell_id.split("-")[1]) for cell_id in v])
                sorted_cells_by_fdn[k] = ["{0}-{1}".format(value_split, cell_no) for cell_no in cell_ids]
        self.sorted_cbrs_cells = sorted_cells_by_fdn

    def get_fru_count(self):
        """
        Parsing the values from Product Data Dictionary to get FRU count on each node
        """
        log.logger.debug("Counting instances of node_ids in Product Data to get fru count.")
        self.fru_dict = {node: 0 for node in self.node_ids}
        for product_data in self.product_data_split:
            for node in self.fru_dict.keys():
                if node in product_data:
                    self.fru_dict[node] += 1
        log.logger.debug("Completed querying deployment for FRU count for each CBRS enabled node.")

    def get_all_product_data(self, user):
        """
        Querying ENM get the product Number of the Device and fru count
        :param user: user object
        :type user: `enmutils.enm_user_2`
        :raises EnvironError: If no product number found
        :raises NoOuputFromScriptEngineResponseError: If no response from ENM
        :raises EnmApplicationError: If there is an error such as a timeout while executing command
        """
        output = ""
        try:
            response = user.enm_execute(PRODUCT_NUMBER_CMD)
            output = response.get_output()
            if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in output):
                raise EnvironError('No Product data found: [{0}]'.format(output))
        except (EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError) as e:
            log.logger.debug('Could not use node, error encountered: [{0}].'.format(str(e)))
        self.product_data_split = re.split("FDN", str(output).replace(":", ""))
        self.product_data_split = self.product_data_split[1:]
        find_all_node_ids = re.findall(r'ManagedElement=(.*?),', str(output))
        self.node_ids = list(set(find_all_node_ids))

    def build_product_data_dict(self):
        """
            Iterates Nodes and product data to build a dictionary for cbrs node data
        """
        log.logger.debug("Started querying deployment for Product Data.")
        log.logger.debug("Need to check {0} node ids in chunks of {1}, in {2} elements of product data. "
                         "This could take a lot of time.".format(len(self.node_ids), CHUNK_SIZE,
                                                                 len(self.product_data_split)))
        for chunk_num, nodes_chunk in enumerate(chunks(self.node_ids, CHUNK_SIZE), 1):
            log.logger.debug("Started querying deployment for Product Data for nodes chunk {0}".format(chunk_num))
            self.build_product_data_dict_per_nodes_chunk(nodes_chunk)
            log.logger.debug("Completed querying deployment for Product Data for nodes chunk {0}".format(chunk_num))
        log.logger.debug("Completed querying deployment for Product Data.")

    def build_product_data_dict_for_validating_device_count(self, node, product_data_split):
        """
        Builds the product data dict for validating device count
        :param node: Node id to identify if its in product data
        :type node: str
        :param product_data_split: Contains a split list of product data as strings
        :type product_data_split:  list
        """
        self.product_data_dict[node] = []
        for product_data in product_data_split:
            device_in_product_data = (PRODUCT_ID_DICT.get(DEVICE_6488) in product_data or
                                      PRODUCT_ID_DICT.get(DEVICE_2208) in product_data or
                                      PRODUCT_ID_DICT.get(DEVICE_4408) in product_data or
                                      PRODUCT_ID_DICT.get(DEVICE_NR_4408) in product_data or
                                      PRODUCT_ID_DICT.get(DEVICE_RADIODOT) in product_data)
            if node in product_data and device_in_product_data:
                self.product_data_dict[node].append(product_data)
                if len(self.product_data_dict[node]) == 120:
                    break

    def build_product_data_dict_per_nodes_chunk(self, nodes_chunk):
        """
        Build product data for each chunk of nodes
        :param nodes_chunk: chunk of node ids to build product data
        :type nodes_chunk: list
        """
        cbrs_keys = self.sorted_cbrs_cells.keys()
        product_data_keys = self.product_data_dict.keys()
        product_data_split = self.product_data_split
        for node in nodes_chunk:
            if (node not in product_data_keys) and (node in cbrs_keys):
                self.build_product_data_dict_for_validating_device_count(node, product_data_split)

    @staticmethod
    def validate_frus(product_data_per_node, device_type):
        """
        Validates frus to get an accurate count of devices for each node
        :param product_data_per_node: product data to check how many devices a node will have
        :type product_data_per_node: list
        :param device_type: Determines which key we check the values for
        :type device_type: str
        :return: device count each node based on the product numbers found in the values
        :rtype: int
        """
        device_count = 0
        if product_data_per_node and PRODUCT_ID_DICT[device_type] in product_data_per_node[0]:
            device_count += 1
        if len(product_data_per_node) > 1 and PRODUCT_ID_DICT[device_type] in product_data_per_node[1]:
            device_count += 1
        return device_count

    def get_device_count_based_on_nr_nodes(self, node_id):
        """
        Based on cell size we can assume groups and thus devices
        :param node_id: Id of the node to add to device_type dict and device_count_dict_per_node dict
        :type node_id: str
        :return: returns the device count of the NR node based on cell size
        :rtype: int
        """
        device_count_node = 0
        if node_id in self.cell_size.get(12):
            device_count_node += 6
        elif node_id in self.cell_size.get(6):
            device_count_node += 3
        elif node_id in self.cell_size.get(3):
            device_count_node += 1

        return device_count_node

    def get_device_count_based_on_frus(self, node_id, product_data_per_node, device_type):
        """
        Adds the nodes into the correct device type dictionary list and adds the device count for each node
        :param node_id: Id of the node to add to device_type dict and device_count_dict_per_node dict
        :type node_id: str
        :param product_data_per_node: list of product data to validate product numbers against
        :type product_data_per_node: list
        :param device_type: Determines which key we add the node too in the device_type dict
        :type device_type: str
        """
        if 'gNodeBRadio' in node_id:
            device_count_node = self.get_device_count_based_on_nr_nodes(node_id)
            self.device_type[device_type].append(node_id)
            self.device_count_dict_per_node[node_id] = device_count_node
        else:
            device_count_node = self.validate_frus(product_data_per_node, device_type)
            if device_count_node > 0:
                self.device_type[device_type].append(node_id)
                self.device_count_dict_per_node[node_id] = device_count_node

    def sort_by_product_data(self, node_id):
        """
        Sorting the product data to get the Device type
        :param node_id: Id of the node to check the key against and to use in get_device_count_based_on_frus
        :type node_id: str
        """
        for key, value in self.product_data_dict.items():
            if node_id == key and len(value) == 0:
                log.logger.debug("First instance of {0} doesn't contain product data {1}".format(node_id, value))
                continue
            elif ("gNodeBRadio" in node_id and node_id == key and key not in self.device_type.get(DEVICE_NR_4408) and
                  PRODUCT_ID_DICT[DEVICE_NR_4408] in str(value[0])):
                self.get_device_count_based_on_frus(node_id, value, DEVICE_NR_4408)
            elif (node_id == key and key not in self.device_type.get(DEVICE_6488) and
                  PRODUCT_ID_DICT[DEVICE_6488] in str(value[0])):
                self.get_device_count_based_on_frus(node_id, value, DEVICE_6488)
            elif (node_id == key and key not in self.device_type.get(DEVICE_2208) and
                  PRODUCT_ID_DICT[DEVICE_2208] in str(value[0])):
                self.get_device_count_based_on_frus(node_id, value, DEVICE_2208)
            elif (node_id == key and key not in self.device_type.get(DEVICE_4408) and
                  PRODUCT_ID_DICT[DEVICE_4408] in str(value[0])):
                self.get_device_count_based_on_frus(node_id, value, DEVICE_4408)

    def sort_radiodots_and_get_device_counts(self, radio_node_id):
        """
        Gets Rf count for the node and counts to checks the number to get the Device count.
        :param radio_node_id: Node identifier
        :type radio_node_id: str
        """
        for node_id, rf_count in self.rf_branch_count_dict.items():
            if radio_node_id == str(node_id):
                if rf_count == 4:
                    self.device_type[DEVICE_RADIODOT].append(node_id)
                    self.device_count_dict_per_node[node_id] = 48
                elif rf_count == 2:
                    self.device_type[DEVICE_RADIODOT].append(node_id)
                    self.device_count_dict_per_node[node_id] = 24
                else:
                    log.logger.debug("{0} has_rf_count of {1}".format(node_id, rf_count))

    def count_all_rf_branches(self):
        """
        Counts the number of node_ids in the rf_data to give the rf count
        """
        log.logger.debug("Starting to count the rf branches this may take some time")
        for node_id, rf_data_list in self.rf_data_dict.items():
            for item in rf_data_list:
                rf_branch_ref_data = re.findall('rfBranchRef(.*?)]', item)
                rf_branch_count = str(rf_branch_ref_data).count(node_id)
                if rf_branch_count == 2 or rf_branch_count == 4 and node_id not in self.rf_branch_count_dict.keys():
                    self.rf_branch_count_dict[node_id] = rf_branch_count
        log.logger.debug("Finished counting the rf branches")

    def get_node_ids_from_rf_data(self, rf_data_split):
        """
        Gets node_ids and adds the keys to the rf_data_dict
        :param rf_data_split: List of rf data split
        :type rf_data_split: List
        """
        log.logger.debug("Getting node_ids for rf dict")
        for rf_data in rf_data_split:
            if "ManagedElement=" in rf_data:
                node_ids = re.findall('ManagedElement=(.*?),', str(rf_data))
                unique_node_id = node_ids[0]
                if unique_node_id not in self.rf_data_dict.keys():
                    self.rf_data_dict[unique_node_id] = []
        log.logger.debug("Finished getting node_ids for rf dict")

    def get_rf_data_per_node_id(self, rf_data_split):
        """
        Gets 6 instances of rf data per node
        :param rf_data_split: List of rf data split
        :type rf_data_split: List
        """
        log.logger.debug("Getting 6 elements of rf data per node id")
        for node in self.rf_data_dict.keys():
            for rf_data in rf_data_split:
                if str(node) in rf_data and len(self.rf_data_dict[node]) < 6:
                    self.rf_data_dict[node].append(rf_data)
        log.logger.debug("Finished getting 6 elements of rf data per node id")

    def get_rf_branch(self, user):
        """
        Querying ENM  Gets the all Rf branch data, splits by the FDN
        :param user: user object
        :type user: `enmutils.enm_user_2`
        :raises EnvironError: If no product number found
        :raises NoOuputFromScriptEngineResponseError: If no response from ENM
        :raises EnmApplicationError: If there is an error such as a timeout while executing command
        """
        output = ""
        try:
            response = user.enm_execute(RF_BRANCH_REF)
            output = response.get_output()
            if any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in output):
                raise EnvironError('No RfBranchRef data found: [{0}]'.format(output))
        except (EnvironError, EnmApplicationError, NoOuputFromScriptEngineResponseError) as e:
            log.logger.debug('Could not use node, error encountered: [{0}].'.format(str(e)))
        rf_data_split = re.split("FDN", str(output).replace(":", ""))
        self.get_node_ids_from_rf_data(rf_data_split)
        self.get_rf_data_per_node_id(rf_data_split)
        self.count_all_rf_branches()

    def sort_device_type(self):
        """
        Sort the node id into device types based upon the cell count and product number
        2208:
            - 6 cell and productNumber is 'KRC 161 711/1'
            - 12 cell and productNumber is 'KRC 161 711/1'
        4408:
            - 3 cell and productNumber is 'KRC 161 746/1'
            - 6 cell and productNumber is 'KRC 161 746/1'
            - 12 cell and productNumber is 'KRC 161 746/1'
        6488:
            -3 cell and productNumber is 'KRD 901 160/11'
            -6 cell and productNumber is 'KRD 901 160/11'
        NR_4408:
            - 3 cell and productNumber is 'KRC 161 746/1'
            - 6 cell and productNumber is 'KRC 161 746/1'
            - 12 cell and productNumber is 'KRC 161 746/1'
        RadioDot:
            - 12 cell and > 40 FRUs 2 rfBranchRef is 2x2 with 24 devices
            - 12 cell and > 40 FRUs 4 rfBranchRef is 4x4 with 48 devices
        """
        log.logger.debug("Sorting CBRS enabled nodes, into respective device types, by FRU count and cell size.")
        for node_id in self.sorted_cbrs_cells.keys():
            if node_id in self.cell_size.get(12) and self.fru_dict.get(node_id) < 2:
                log.logger.debug("{0} doesnt meet the criteria as it has {1} and 12 cells".format(node_id,
                                                                                                  self.fru_dict.get(
                                                                                                      node_id)))
            elif node_id in self.cell_size.get(12) and self.fru_dict.get(node_id) > 40:
                self.sort_radiodots_and_get_device_counts(node_id)
            elif (node_id in self.cell_size.get(12) or node_id in self.cell_size.get(6) or
                  node_id in self.cell_size.get(3)):
                self.sort_by_product_data(node_id)
        log.logger.debug("Completed sort of CBRS enabled nodes, into respective device types, by FRU count and cell "
                         "size.")

    def get_required_number_of_devices(self):
        """
        Determine how many devices are required per device type, select nodes until device count is reached.
        """
        log.logger.debug("Selecting number of devices required by device type and availability.")
        self.nodes_selected_by_device_type = {key: [] for key in self.DEVICES_REQUIRED.keys()}
        for device_type, num_required in self.DEVICES_REQUIRED.items():
            device_count = 0
            if not self.device_type.get(device_type):
                log.logger.debug("No available {0} devices found.".format(device_type))
                continue
            for node_id in self.device_type.get(device_type):
                if node_id not in self.used_nodes and device_count < num_required and device_type != DEVICE_PASSIVE_DAS_4408:
                    self.nodes_selected_by_device_type[device_type].append(node_id)
                    device_count += self.device_count_dict_per_node.get(node_id)
                    self.device_count_dict_by_device_type[device_type] += self.device_count_dict_per_node.get(node_id)
                    self.used_nodes.append(node_id)
                elif node_id not in self.used_nodes and device_count < num_required and device_type == DEVICE_PASSIVE_DAS_4408:
                    self.nodes_selected_by_device_type[device_type].append(node_id)
                    device_count += 10
                    self.device_count_dict_by_device_type[device_type] += 10
                    self.used_nodes.append(node_id)
                    self.passive_das_4408_nodes.append(node_id)
        log.logger.debug("Completed selecting number of devices required by device type and availability.")

    def generate_cbrs_add_commands(self):
        """
        Build the CBRS add commands based upon the selected nodes
        """
        log.logger.debug("Building list of CBRS add command.")
        for node_id in self.used_nodes:
            if "gNodeBRadio" in node_id:
                cells_to_add, groups_to_create = self.determine_num_cells_to_add_and_groups_required_for_nr_nodes(
                    node_id)
            else:
                cells_to_add, groups_to_create = self.determine_num_cells_to_add_and_groups_required(node_id)
            fdn_list = self.sorted_cbrs_cells.get(node_id)
            if (cells_to_add * groups_to_create) == len(fdn_list):
                subnetwork = '{0}|'.format('|'.join(re.findall("SubNetwork=(.*?),", fdn_list[0])))
                groups_created, start_index, end_index = 0, 0, cells_to_add
                while groups_created < groups_to_create:
                    group = self.select_cells(start_index, end_index, fdn_list)
                    if "gNodeBRadio" in node_id:
                        self.add_group_commands.append(
                            NR_BASE_ADD_CMD.format(subnetwork, node_id, node_id, ','.join(group)))
                    else:
                        self.add_group_commands.append(BASE_ADD_CMD.format(subnetwork, node_id, ','.join(group)))
                    self.cell_grouping_for_pal_policies.append("{0}:{1}".format(node_id, ','.join(group)))
                    groups_created += 1
                    start_index += cells_to_add
                    end_index += cells_to_add
            else:
                log.logger.debug("{0} doesnt meet the criteria as its cells {1} by its groups {2} dont match cell count {3}".format(node_id, cells_to_add, groups_to_create, len(fdn_list)))
        self.add_group_commands = sorted(set(self.add_group_commands))
        log.logger.debug("Completed building list of CBRS add command, total commands to be executed: [{0}].".format(
            len(self.add_group_commands)))
        self.update_nodes_used_by_profile(set(self.used_nodes))

    def determine_num_cells_to_add_and_groups_required_for_nr_nodes(self, node_id):
        """
        Determine how many cells and groups need to be created for nr nodes based upon the device type
        NR 4408:
            -3 Cell nodes has 1 group and 2 cells - 1 device
            -6 Cell nodes has 3 group and 2 cells - 3 devices
            -12 Cell nodes has 6 group and 2 cells - 6 devices

        :param node_id: Id of the node to determine cells and groups for.
        :type node_id: str

        :return: Tuple containing the number of cells to add and the number of groups to create
        :rtype: tuple
        """
        if ("gNodeBRadio" in node_id and node_id in self.device_type.get(DEVICE_NR_4408) and
                self.device_count_dict_per_node.get(node_id) == 6 and node_id in self.cell_size.get(12)):
            cells_to_add = 2
            groups_to_create = 6
        elif ("gNodeBRadio" in node_id and node_id in self.device_type.get(DEVICE_NR_4408) and
              self.device_count_dict_per_node.get(node_id) == 3 and node_id in self.cell_size.get(6)):
            cells_to_add = 2
            groups_to_create = 3
        else:
            cells_to_add = 2
            groups_to_create = 1
        return cells_to_add, groups_to_create

    def determine_num_cells_to_add_and_groups_required(self, node_id):
        """
        Determine how many cells and groups need to be created based upon the device type
        2208:
            - 3 Cells and 2 Groups
        6488 and 4408:
            - 3 Cells and 1 Group for 3 cell nodes
        6488 and 4408:
            - 6 Cells and 1 Group for 6 cell nodes
        4408:
            - 6 Cells and 2 Group for 12 cell nodes
        RadioDot:
            - 4 Cells and 3 Groups for 2x2
            - 2 cells and 6 group for 4x4

        :param node_id: Id of the node to determine cells and groups for.
        :type node_id: str

        :return: Tuple containing the number of cells to add and the number of groups to create
        :rtype: tuple
        """
        if (node_id in self.device_type.get(DEVICE_4408) and self.device_count_dict_per_node.get(
                node_id) == 2 and node_id in self.cell_size.get(12)):
            cells_to_add = 6
            groups_to_create = 2
        elif ((node_id in self.device_type.get(DEVICE_4408) or node_id in self.device_type.get(DEVICE_6488)) and
              self.device_count_dict_per_node.get(node_id) == 1 and node_id in self.cell_size.get(6)):
            cells_to_add = 6
            groups_to_create = 1
        elif node_id in self.device_type.get(DEVICE_2208) and self.device_count_dict_per_node.get(node_id) == 2:
            cells_to_add = 3
            groups_to_create = 2
        elif ((node_id in self.device_type.get(DEVICE_6488) or node_id in self.device_type.get(DEVICE_4408)) and
              self.device_count_dict_per_node.get(node_id) == 1 and node_id in self.cell_size.get(3)):
            cells_to_add = 3
            groups_to_create = 1
        elif node_id in self.device_type.get(DEVICE_RADIODOT) and self.device_count_dict_per_node.get(node_id) == 24:
            cells_to_add = 4
            groups_to_create = 3
        elif node_id in self.device_type.get(DEVICE_RADIODOT) and self.device_count_dict_per_node.get(node_id) == 48:
            cells_to_add = 2
            groups_to_create = 6
        else:
            cells_to_add = 0
            groups_to_create = 0
            log.logger.debug("Unable to get correct groups for {0} and {1} devices".format(
                node_id, self.device_count_dict_per_node.get(node_id)))
        return cells_to_add, groups_to_create

    @staticmethod
    def select_cells(start_cell_index, end_cell_index, fdn_list):
        """
        Select the required number of cell names from the supplied list.

        :param start_cell_index: FDN to start selection
        :type start_cell_index: int
        :param end_cell_index: FDN to finish selection
        :type end_cell_index: int
        :param fdn_list: List of Node FDNs to extract the cell name(s) from
        :type fdn_list: list
        :return: List of selected cell names.
        :rtype: list
        """
        cell_names = []
        for fdn in fdn_list[start_cell_index:end_cell_index]:
            if "gNodeBRadio" in fdn:
                cell_names.append(re.findall('NRSectorCarrier=(.*)', fdn)[0])
            else:
                cell_names.append(re.findall('EUtranCellTDD=(.*)', fdn)[0])
        return cell_names

    @retry(retry_on_exception=lambda e: isinstance(e, (EnvironError, EnmApplicationError,
                                                       NoOuputFromScriptEngineResponseError)),
           wait_exponential_multiplier=30000, stop_max_attempt_number=3)
    def run_remote_cbrs_add_cmd(self, command, admin_user, sleep_time):
        """
        Runs Cbrs commands to scripting vm using scripting service ips

        :param command: Command to be executed
        :type command: str
        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User
        :param sleep_time: Sleep time to confirm if groups added
        :type sleep_time: int

        :raises EnmApplicationError: raised if the stdout from command is invalid
        """
        cmd = Command(command, timeout=300)
        response = run_remote_cmd(cmd, random.choice(self.scripting_vms_without_ports), admin_user.username,
                                  admin_user.password)
        if response.ok and response.stdout.strip():
            log.logger.debug("Successfully executed command\t{0}.".format(command))
            log.logger.debug('Sleeping for {0}s to allow group to populate'.format(sleep_time))
            time.sleep(sleep_time)
        else:
            raise EnmApplicationError('Cbrs add command returned status code {0} and no output. Check logs '
                                      'for more details'.format(response.rc))

    def determine_device_type_for_groups(self):
        """
        Function to get groups separated by device type and also count the number of groups available for to be used
        """
        log.logger.debug("Determining the device type for pal groups")
        for node_id in self.used_nodes:
            for group in self.cell_grouping_for_pal_policies:
                if node_id in self.device_type.get(DEVICE_4408) and node_id in group:
                    self.groups_for_each_device_type[DEVICE_4408].append(group)
                    self.groups_available_for_pal[DEVICE_4408] += 1
                elif node_id in self.device_type.get(DEVICE_6488) and node_id in group:
                    self.groups_for_each_device_type[DEVICE_6488].append(group)
                    self.groups_available_for_pal[DEVICE_6488] += 1
        log.logger.debug("Groups available for each device type are : {0}".format(self.groups_available_for_pal))
        log.logger.debug("Finished counting and sorting groups by device types")

    def get_number_of_groups_required_for_device_type(self):
        """
        Function gets the n % which we require pal policies to be executed on.
        """
        log.logger.debug("Getting the percentage of groups required for channel mask and mixpal channel mask")
        percentage_required = self.CBRS_PAL_PERCENTAGE
        for device_type, groups_available in self.groups_available_for_pal.items():
            if device_type == DEVICE_4408 and groups_available > 0:
                pal_groups_required = groups_available * percentage_required
                self.groups_wanted_for_pal_policies[DEVICE_4408] += round(pal_groups_required)
            elif device_type == DEVICE_6488 and groups_available > 0:
                pal_groups_required = groups_available * percentage_required
                self.groups_wanted_for_pal_policies[DEVICE_6488] += round(pal_groups_required)
        log.logger.debug(
            "Number of groups required for each device type is : {0}".format(self.groups_wanted_for_pal_policies))

    def create_xml_file(self):
        """
        Creates a csv file at home/enmutils/cbrs
        """
        log.logger.debug("Creating cert and trust distribution file")
        self.batch_num_required = int(ceil(len(self.used_nodes) / 1200.0))
        self.batch_num_required += 1
        for current_batch_num in range(1, self.batch_num_required):
            file_name = XML_FILE_NAME.format(current_batch_num)
            self.end_range_for_batch = current_batch_num * 1200 - current_batch_num
            with open(XML_CERT_DIR.format(file_name), "w") as xml_file:
                xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                xml_file.write("<Nodes>\n")
                for node_id in self.used_nodes[self.start_range_for_batch:self.end_range_for_batch]:
                    if self.batch_node_count <= self.end_range_for_batch:
                        xml_file.write("\t<Node>\n")
                        xml_file.write("\t\t<NodeFdn>{0}</NodeFdn>\n".format(node_id))
                        xml_file.write("\t</Node>\n")
                        self.batch_node_count += 1
                xml_file.write("</Nodes>\n")
                self.start_range_for_batch = self.end_range_for_batch
                self.trust_cert_xml_list.append(file_name)
        log.logger.debug("xml_files_created: {0}".format(self.trust_cert_xml_list))
        log.logger.debug("Finished creating XML files")

    def run_sec_admin_command_on_nodes(self, user):
        """
        Run secadm command on trust cert xml file
        :param user: user object
        :type user: `enmutils.enm_user_2`
        """
        log.logger.debug("Executing Secadm command for trust certs")
        for isfile in self.trust_cert_xml_list:
            response = user.enm_execute(TRUST_CERT_PRE.format(isfile), file_in=XML_CERT_DIR.format(isfile))
            output = response.get_output()
            log.logger.debug("Response to Trust cert command : {0}".format(output))
            job_status_command = re.findall("'(.*)' ", str(output))
            job_status_command = str(job_status_command).strip('[]')
            job_status_command = job_status_command[1:-1]
            log.logger.debug("job_command : {0}".format(job_status_command))
            for current_poll in range(CERT_POLL_COUNT):
                response = user.enm_execute(job_status_command)
                output = response.get_output()
                if 'COMPLETED' not in str(output) and current_poll + 1 != CERT_POLL_COUNT:
                    log.logger.debug(
                        "job has not yet completed Sleeping for 100 seconds and will prompt again ({0}/{1})".format(current_poll, CERT_POLL_COUNT))
                    time.sleep(CERT_POLL_TIMER)
                elif 'COMPLETED' in str(output):
                    log.logger.debug('JOB in completed state after {0}/{1} iterations'.format(current_poll, CERT_POLL_COUNT))
                    break
                else:
                    log.logger.debug('Failed_trust_cert_status on: {0}'.format(TRUST_CERT_PRE.format(isfile)))
                    self.failed_trust_cert_xmls.append(TRUST_CERT_PRE.format(isfile))
            log.logger.debug("Finished executing Secadm command for trust certs")

    def cert_and_trust_distribution_on_nodes(self, user):
        """
        Creates xml file and runs secadm command on ENM

        :param user: user object
        :type user: `enmutils.enm_user_2`
        """
        log.logger.debug("Creating xml for cert creation on nodes")
        self.create_xml_file()
        self.run_sec_admin_command_on_nodes(user)
        log.logger.debug("Finished Creating xml for cert creation on nodes")

    def create_maintenance_user_mo_on_node(self, user):
        """
        Creates the maintenance user mo on nodes used by the profile, Errors are logged and not raised

        :param user: user object
        :type user: `enmutils.enm_user_2`
        """
        if self.SA_DC_CLUSTER_IP_LIST != '':
            log.logger.debug("Creating MaintenanceUser MO on Nodes")
            for node_id in self.used_nodes:
                try:
                    if 'gNodeB' in node_id:
                        user.enm_execute(CREATE_MAINTENANCE_USER_MO_NR.format(node_id))
                    else:
                        user.enm_execute(CREATE_MAINTENANCE_USER_MO_LTE.format(node_id))
                except (NoOuputFromScriptEngineResponseError, OSError, EnmApplicationError) as e:
                    self.failed_maintenance_user_created_nodes.append(node_id)
                    log.logger.debug("Error occured while creating MaintenanceUser MO on {0}, error is: [{1}]".format(node_id, e))
        log.logger.debug("Finished Creating MaintenanceUser MO on Nodes")

    def map_nodes_to_standalone_domain_coordinator(self, admin_user):
        """
        Maps nodes to the Standalone domain coordinator
        cbrs set --cbrsfunction <IP Address> "<SubNetwork> ManagedElement=<Node name>"
        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Mapping Nodes to the Standalone Domain Coordinator")
        if self.SA_DC_CLUSTER_IP_LIST:
            for node_id in self.used_nodes:
                if 'gNodeBRadio' not in node_id:
                    mapping_path = LTE_MAPPING_SUBNETWORK.format(node_id)
                else:
                    mapping_path = NR_MAPPING_SUBNETWORK.format(node_id)
                try:
                    self.run_remote_cbrs_add_cmd(MAP_NODES_TO_SA_DC.format(self.SA_DC_CLUSTER_IP_LIST, mapping_path),
                                                 admin_user, sleep_time=1)
                    self.mapped_paths_for_nodes.append(mapping_path)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
        log.logger.debug("Finished Mapping nodes for SA DC")

    def set_standalone_domain_coordinator(self, admin_user):
        """
        Sets Both SAS URL AND / OR SA DC CLUSTER
        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Checking if profile can be used for Phase 1B")
        if self.SAS_URL != '':
            log.logger.debug("SAS URL SET IN CONFIG")
            if self.SA_DC_CLUSTER_IP_LIST:
                log.logger.debug("SA DC LIST SET IN CONFIG")
                try:
                    self.run_remote_cbrs_add_cmd(SET_SA_DC_AND_SAS_URL.format(self.SA_DC_CLUSTER_IP_LIST, self.SAS_URL),
                                                 admin_user, sleep_time=1)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
            else:
                try:
                    self.run_remote_cbrs_add_cmd(SET_SAS_URL.format(self.SAS_URL), admin_user, sleep_time=1)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
        log.logger.debug("Set standalone domain coordinator Successfully ")

    def cleanup_mapped_nodes_on_teardown(self, user):
        """
        Set nodes back to default mapping of ENM
        :param user: User who will execute the commands on the scripting cluster
        :type user: `enm_user_2.User`
        """
        log.logger.debug("Un-Mapping Nodes on Teardown")
        if self.SA_DC_CLUSTER_IP_LIST:
            for node_mapped in self.mapped_paths_for_nodes:
                try:
                    self.run_remote_cbrs_add_cmd(UNMAP_NODES_TO_SA_DC.format(node_mapped), user, sleep_time=1)
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
        log.logger.debug("Finished Un-Mapping Nodes")

    def get_groups_for_mixpalgaa(self):
        """
        Function gets the groups to be set for mixpalgaa
        """
        log.logger.debug("Getting the percentage of groups required for mixpalgaa policies")
        device_types = self.groups_for_each_device_type.keys()
        for device_type in device_types:
            group_count = 0
            for group in self.pal_4408_groups_used:
                if device_type == DEVICE_4408 and group_count < self.groups_wanted_for_mixpalgaa.get(device_type):
                    self.mixpalgaa_4408_groups_used.append(group)
                    group_count += 1
            for group in self.pal_6488_groups_used:
                if device_type == DEVICE_6488 and group_count < self.groups_wanted_for_mixpalgaa.get(device_type):
                    self.mixpalgaa_6488_groups_used.append(group)
                    group_count += 1
        log.logger.debug('Finished getting the groups for pal mixpalgaa')

    def get_groups_for_pal_policies(self):
        """
        Function to get the number of groups for masks to be changed on for pal to executed on
        """
        log.logger.debug("Getting the groups for channel and mixpal channel mask")
        device_types = self.groups_for_each_device_type.keys()
        for device_type in device_types:
            group_count = 0
            for group in self.groups_for_each_device_type.get(device_type):
                if device_type == DEVICE_4408 and group_count < self.groups_wanted_for_pal_policies.get(device_type):
                    self.pal_4408_groups_used.append(group)
                    group_count += 1
                elif device_type == DEVICE_6488 and group_count < self.groups_wanted_for_pal_policies.get(device_type):
                    self.pal_6488_groups_used.append(group)
                    group_count += 1
        log.logger.debug('Finished getting the groups for pal policies')

    def get_required_amount_of_groups_mixpalgaa(self):
        """
        Gets the required amount of mixpalgaa groups required to be set
        """
        log.logger.debug("Getting the groups required for mixpalgaa policies")
        mixpalgaa_percentage = self.MIXPALGAA_PERCENTAGE
        for device_type, groups_available in self.groups_wanted_for_pal_policies.items():
            if device_type == DEVICE_4408 and groups_available > 0:
                mixpalgaa_groups_required = groups_available * mixpalgaa_percentage
                self.groups_wanted_for_mixpalgaa[DEVICE_4408] += round(mixpalgaa_groups_required)
            elif device_type == DEVICE_6488 and groups_available > 0:
                mixpalgaa_groups_required = groups_available * mixpalgaa_percentage
                self.groups_wanted_for_mixpalgaa[DEVICE_6488] += round(mixpalgaa_groups_required)
        log.logger.debug("groups_wanted_for_mixpalgaa : {0}".format(self.groups_wanted_for_mixpalgaa))

    def set_pal_policies_for_cbrs_groups(self, user):
        """
        This Function gets the required number of groups for pal, selects the groups and sets the commands

        :param user: User who will execute the commands on the scripting cluster
        :type user: `enm_user_2.User`
        """
        self.determine_device_type_for_groups()
        self.get_number_of_groups_required_for_device_type()
        self.get_required_amount_of_groups_mixpalgaa()
        self.get_groups_for_pal_policies()
        self.get_groups_for_mixpalgaa()
        self.set_6488_channel_mask_and_mixpal_channel_mask(user)
        self.set_4408_channel_mask_and_mixpal_channel_mask(user)
        self.set_mixpalgaa_policies(user)

    def set_4408_channel_mask_and_mixpal_channel_mask(self, admin_user):
        """
        Function to set the channel mask and mixpal channel mask

        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Setting policies for 4408 DEVICES")
        for node_id in self.used_nodes:
            fdn_list = self.sorted_cbrs_cells.get(node_id)
            subnetwork = '{0}|'.format('|'.join(re.findall("SubNetwork=(.*?),", fdn_list[0])))
            for group in self.pal_4408_groups_used:
                if node_id in group:
                    try:
                        self.run_remote_cbrs_add_cmd(SET_CHANNEL_MASK.format('111111111111100', subnetwork, group),
                                                     admin_user, sleep_time=1)
                        self.run_remote_cbrs_add_cmd(SET_MIXPAL_CHANNEL_MASK.format("true", subnetwork, group),
                                                     admin_user, sleep_time=1)
                    except Exception as e:
                        self.add_error_as_exception(EnmApplicationError(e))

    def set_6488_channel_mask_and_mixpal_channel_mask(self, admin_user):
        """
        Function to set the channel mask and mixpal channel mask

        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Setting policies for 6488 DEVICES")
        for node_id in self.used_nodes:
            fdn_list = self.sorted_cbrs_cells.get(node_id)
            subnetwork = '{0}|'.format('|'.join(re.findall("SubNetwork=(.*?),", fdn_list[0])))
            for group in self.pal_6488_groups_used:
                if node_id in group:
                    try:
                        self.run_remote_cbrs_add_cmd(SET_CHANNEL_MASK.format('111111000000000', subnetwork, group),
                                                     admin_user, sleep_time=1)
                        self.run_remote_cbrs_add_cmd(SET_MIXPAL_CHANNEL_MASK.format("true", subnetwork, group),
                                                     admin_user, sleep_time=1)
                    except Exception as e:
                        self.add_error_as_exception(EnmApplicationError(e))

    def set_mixpalgaa_policies(self, admin_user):
        """
        Setting Mixpalgaa polocies for 4408 and 6488 Devices
        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Setting mixpalgaa policies")
        for node_id in self.used_nodes:
            fdn_list = self.sorted_cbrs_cells.get(node_id)
            subnetwork = '{0}|'.format('|'.join(re.findall("SubNetwork=(.*?),", fdn_list[0])))
            for group_list in self.lists_mixpalgaa_groups_used:
                for group in group_list:
                    if node_id in group:
                        try:
                            self.run_remote_cbrs_add_cmd(SET_MIXPALGAA.format("false", subnetwork, group), admin_user,
                                                         sleep_time=1)
                        except Exception as e:
                            self.add_error_as_exception(EnmApplicationError(e))

    def teardown_pal_policies(self, user):
        """
        Function unsets any policies changed by the profile on teardown

        :param user: User who will execute the commands on the scripting cluster
        :type user: `enm_user_2.User`
        """
        self.unset_channel_mask_and_mixpal_channel_mask_on_teardown(user)
        self.unset_mixpalgaa_policies_on_teardown(user)

    def unset_channel_mask_and_mixpal_channel_mask_on_teardown(self, admin_user):
        """
        Unsetting channel masks and mixpal channel masks on teardown
        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Unsetting channel mask and mixpal channel mask on Teardown")
        for node_id in self.used_nodes:
            fdn_list = self.sorted_cbrs_cells.get(node_id)
            subnetwork = '{0}|'.format('|'.join(re.findall("SubNetwork=(.*?),", fdn_list[0])))
            for group_list in self.lists_pal_groups_used:
                for group in group_list:
                    if node_id in group:
                        try:
                            self.run_remote_cbrs_add_cmd(SET_CHANNEL_MASK.format('111111111111111', subnetwork, group),
                                                         admin_user, sleep_time=1)
                            self.run_remote_cbrs_add_cmd(SET_MIXPAL_CHANNEL_MASK.format("false", subnetwork, group),
                                                         admin_user, sleep_time=1)
                        except Exception as e:
                            self.add_error_as_exception(EnmApplicationError(e))

    def unset_mixpalgaa_policies_on_teardown(self, admin_user):
        """
        Unsets the mixpalgaa policies which we had set.
        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug("Unsetting mixpalgaa policies on teardown")
        for node_id in self.used_nodes:
            fdn_list = self.sorted_cbrs_cells.get(node_id)
            subnetwork = '{0}|'.format('|'.join(re.findall("SubNetwork=(.*?),", fdn_list[0])))
            for group_list in self.lists_mixpalgaa_groups_used:
                for group in group_list:
                    if node_id in group:
                        try:
                            self.run_remote_cbrs_add_cmd(SET_MIXPALGAA.format("true", subnetwork, group), admin_user,
                                                         sleep_time=1)
                        except Exception as e:
                            self.add_error_as_exception(EnmApplicationError(e))

    def execute_cbrs_add_commands(self, admin_user):
        """
        Executes CBRS add commands

        :param admin_user: User who will execute the commands on the scripting cluster
        :type admin_user: `enm_user_2.User`
        """
        log.logger.debug('Total groups to add {0}'.format(len(self.add_group_commands)))
        for command in self.add_group_commands:
            try:
                self.run_remote_cbrs_add_cmd(command, admin_user, sleep_time=3)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
        log.logger.debug("Finished adding groups")

    def update_nodes_used_by_profile(self, used_nodes=None):
        """
        Remove used nodes from the profile.
        :param used_nodes: Set of nodes ids the profile is will use.
        :type used_nodes: set
        """
        log.logger.debug('used nodes {0}'.format(used_nodes))
        used_nodes = used_nodes if used_nodes else []
        unused_nodes = [node for node in self.lite_nodes
                        if node.node_id not in used_nodes]
        if unused_nodes:
            self.update_profile_persistence_nodes_list(unused_nodes)

    @retry(retry_on_exception=lambda e: isinstance(e, RuntimeError), wait_fixed=30000,
           stop_max_attempt_number=3)
    def remove_groups(self, user, scripting_vms):
        """
        Remove cbrs groups. Remove all groups by default.
        :param user: user object
        :type user: `enmutils.enm_user_2`
        :param scripting_vms: List of scripting vms
        :type scripting_vms: list
        :return: Command executed successfully or not
        :rtype: bool
        """
        scripting_vm = random.choice(scripting_vms)
        if self.SA_DC_CLUSTER_IP_LIST != '':
            remove_cmd = (Command('cbrs remove --deregister all --cbrsfunction {0} --quiet'.format(self.SA_DC_CLUSTER_IP_LIST)))
        else:
            remove_cmd = (Command('cbrs remove --deregister all --quiet'))
        response = run_cmd_on_vm(remove_cmd, scripting_vm, user=user.username, password=user.password)
        log.logger.debug('{0} executed on scripting vm {1} with status code {2}'.format(response.command, scripting_vm,
                                                                                        response.rc))
        log.logger.debug('Sleeping for 300s to ensure groups removed')
        time.sleep(60 * 5)
        return True if response.ok else False

    def remove_trust_cert_xml_on_teardown(self):
        """
        Removes trust cert xml on teardown
        """
        log.logger.debug("Removing /home/enmutils/cbrs/trust_cert_file.xml")
        for xmlfile in self.trust_cert_xml_list:
            run_local_cmd("rm -f {0}".format(xmlfile))
        log.logger.debug("Finished Removing /home/enmutils/cbrs/trust_cert_file.xml")
