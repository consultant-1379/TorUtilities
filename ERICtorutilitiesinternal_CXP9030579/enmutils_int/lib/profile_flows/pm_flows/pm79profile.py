import json
from datetime import datetime
from random import shuffle
from functools import partial
from enmutils.lib.timestamp import convert_time_to_ms_since_epoch
from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.profile_flows.pm_flows.pm52profile import (Pm52Profile, get_rfport_fdn_list_from_enm,
                                                                 check_and_remove_old_ulsas_in_enm)
from enmutils_int.lib.node_pool_mgr import group_nodes_per_ne_type


START_ULSA_SAMPLING = "pmul-service/rest/command/start"
STOP_ULSA_SAMPLING = ("pmul-service/rest/command/stop/node/{node_name}/ulsa/{ulsa_id}/port/{rfport_ldn}/"
                      "samplingType/SCHEDULED")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
SAMPLINGTIMEOUT_PARAMETER = 0
SAMPLINGINTERVAL_PARAMETER = 5
CENTERFREQUENCY_KHZ = 678175
DISPLAYEDBANDWIDTH_KHZ = 12
RESOLUTIONDBANDWIDTH_KHZ = 12
SAMPLINGSTART_PARAMETER = 0


def stop_ulsa_uplink_measurement(node_info, user):
    """
    Stop Scheduled Uplink Spectrum Sampling on a node

    :param node_info: Details of Node where sampling will be started
    :type node_info: dict
    :param user: User that will execute the ENM commands
    :type user: enmutils.lib.enm_user_2.User

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    node_name = node_info.keys()[0]
    rfport_ldn = node_info[node_name]['node_rfport_fdn_list']

    log.logger.debug("User {0} is stopping Scheduled Uplink Spectrum Sampling on node {1}"
                     .format(user.username, node_name))
    log.logger.debug("Node_information: {0}".format(node_info))

    failures_occurred = False
    node_rfport_fdn_list_index = 0
    try:
        ulsa_id = 0
        updated_rfport_ldn = rfport_ldn[node_rfport_fdn_list_index]
        response = user.put(STOP_ULSA_SAMPLING.format(node_name=node_name, ulsa_id=ulsa_id,
                                                      rfport_ldn=updated_rfport_ldn))
        raise_for_status(response, message_prefix='Could not stop uplink measurements for node {0}'
                         .format(node_name))
        if "STOPPED" not in response.content:
            log.logger.debug("Unsuccessful result - expecting 'STOPPED' response from ENM on node {0}".format(node_name))
            failures_occurred = True

    except Exception as e:
        log.logger.debug("{0}:exception has been raised while stopping uplink spectrum sampling".format(e))
        failures_occurred = True

    if failures_occurred:
        raise EnmApplicationError("Failures occured while stopping Uplink sampling on node {0}".format(node_name))


def start_ulsa_uplink_measurement(node_info, user):
    """
    Start Scheduled Uplink Spectrum Sampling on a node

    :param node_info: Details of Node where sampling will be started
    :type node_info: dict
    :param user: User that will execute the commands to start the UlSA measurements.
    :type user: enmutils.lib.enm_user_2.User

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    node_name = node_info.keys()[0]
    rfport_ldn = node_info[node_name]['node_rfport_fdn_list']

    log.logger.debug("User {0} is starting Scheduled Uplink Spectrum Sampling on node {1} Node_information: {2}"
                     .format(user.username, node_name, node_info))
    current_date = datetime.now().date()
    SAMPLINGSTART_PARAMETER = convert_time_to_ms_since_epoch(str(current_date), '12:00:00')
    SAMPLINGTIMEOUT_PARAMETER = convert_time_to_ms_since_epoch(str(current_date), '18:00:00')

    failures_occurred = False
    node_rfport_fdn_list_index = 0

    json_data = {
        "nodeId": node_name,
        "ulsaStartPortParameter": rfport_ldn[node_rfport_fdn_list_index],
        "ulsaStartCenterFrequencyParameter": CENTERFREQUENCY_KHZ,
        "ulsaStartResolutionBandwidthParameter": RESOLUTIONDBANDWIDTH_KHZ,
        "ulsaStartDisplayedBandwidthParameter": DISPLAYEDBANDWIDTH_KHZ,
        "scheduler": {
            "ulsaStartSamplingIntervalParameter": SAMPLINGINTERVAL_PARAMETER,
            "ulsaStartScheduledStartTimeParameter": SAMPLINGSTART_PARAMETER,
            "ulsaStartScheduledEndTimeParameter": SAMPLINGTIMEOUT_PARAMETER,
            "ulsaStartScheduledRangesOfHours": "13-14,15-16,17-18"
        },
        "ulsaStartSamplingTypeParameter": "SCHEDULED_SAMPLING",
        "ulsaMoName": "0",
        "policy": {
            "fileHandling": {
                "retainspectrumfile": True,
                "retainsamplefile": False,
                "compressspectrumfile": True
            }
        }
    }

    response = user.post(START_ULSA_SAMPLING, data=json.dumps(json_data), headers=HEADERS)
    raise_for_status(response, message_prefix='Could not start uplink sampling for node {0}'.format(node_name))

    if "triggeredat" not in response.content:
        log.logger.debug("Unsuccessful result - expecting 'triggerdat' key in response from ENM")
        failures_occurred = True

    if not failures_occurred:
        log.logger.debug(
            "Operation to start Scheduled Uplink Spectrum Sampling on node {0} has completed successfully".format(
                node_name))
    else:
        raise EnmApplicationError("Failures occurred while starting Uplink sampling on node {0}".format(node_name))


def perform_teardown_actions(user, selected_nodes):
    """
    Performs the Teardown actions, i.e. stop the ULSA sampling then delete the profile-created ULSA MO's
    :param user: User object. User that runs the cmcli commands.
    :type user: enmutils.lib.enm_user_2.User
    :param selected_nodes: Dictionary of node & MO related info
    :type selected_nodes: dictionary
    """
    log.logger.debug("Performing teardown actions: 1) Stop ULSA sampling 2) Delete profile-created MO's")
    for node_type in selected_nodes:
        for node_name in selected_nodes[node_type]:
            node_info = {node_name: selected_nodes[node_type][node_name]}
            stop_ulsa_uplink_measurement(node_info, user)


class Pm79Profile(Pm52Profile):
    USER = None
    USER_ROLES = []
    SUPPORTED_NODE_TYPES = []
    SCHEDULED_TIMES_STRINGS = []

    def create_and_execute_threads_ulsa(self, selected_nodes):
        """
        Convert the dict with all the candidate nodes to a list, then use it to execute thread tasks

        :param selected_nodes: Lists of candidate nodes, divided by node type.
        :type selected_nodes: dict
        """
        log.logger.debug("Create threads to run against each node")
        selected_nodes_per_type = []
        for node_type in selected_nodes:
            for node_name in selected_nodes[node_type]:
                selected_nodes_per_type.append({node_name: selected_nodes[node_type][node_name]})

        log.logger.debug("Data being used for start/stop operations: {0}".format(selected_nodes_per_type))
        tq = ThreadQueue(selected_nodes_per_type, len(selected_nodes_per_type),
                         func_ref=start_ulsa_uplink_measurement, args=[self.USER])
        tq.execute()

        log.logger.debug("Iteration complete. Checking for errored threads")
        self.show_errored_threads(tq, len(selected_nodes_per_type), EnvironError)

    def select_nodes_from_pool_that_contain_rfport_mo(self, node_type, nodes, rfport_fdn_list):
        """
        Select Nodes from pool that contain RfPort MO

        :param node_type: Type of Node, e.g. ERBS, RadioNode
        :type node_type: str
        :param nodes: List of Node objects
        :type nodes: list
        :param rfport_fdn_list: List of RfPort FDN's in ENM
        :type rfport_fdn_list:  list
        :return: Dictionary of Required number of Nodes and 1 RfPort MO for each
        :rtype: dict
        """
        log.logger.debug("Picking {0} Node(s) from pool having RfPort MO ..."
                         .format(node_type))

        nodes_with_rfport_mos = {}

        possible_nodes = [node for node in nodes if node.primary_type == node_type]
        log.logger.debug('')
        for node in possible_nodes:
            list_of_rfport_fdns = [fdn for fdn in rfport_fdn_list if "{0},".format(node.node_id) in fdn]
            if list_of_rfport_fdns:
                nodes_with_rfport_mos[node.node_id] = {'node': node, 'node_rfport_fdn_list': list_of_rfport_fdns}

        if len(nodes_with_rfport_mos.keys()) == 0:
            self.add_error_as_exception(EnvironError("Unable to select {0} nodes containing "
                                                     "RfPort MO".format(node_type)))
        return nodes_with_rfport_mos

    def select_nodes_to_use(self, user, nodes_list):
        """
        Pick nodes from the pool that have RfPort MO and if necessary create required number of ULSA MO's on these nodes

        :param user: User that will execute the ENM commands
        :type user: enmutils.lib.enm_user_2.User
        :param nodes_list: List of Node objects allocated to profile
        :type nodes_list: list

        :return: Dictionary of candidate nodes per node type, containing RfPort & ULSA fdn's info for each node
        :rtype: dict
        """
        log.logger.debug("Selecting specific nodes from all nodes allocated to profile")
        selected_nodes = {}
        total_selected_nodes = []
        nodes_with_ne_type = group_nodes_per_ne_type(nodes_list)
        synced_nodes = self.get_synchronised_nodes(nodes_list, user)
        rfport_fdn_list = self.get_rfport_fdn_list_from_profile_allocated_nodes(nodes_list)
        log.logger.debug("Exclude nodes that dont have RfPort MO's from all synced nodes")
        for node_type in self.NUM_NODES.keys():
            if node_type in nodes_with_ne_type and nodes_with_ne_type[node_type]:
                nodes_found = self.select_nodes_from_pool_that_contain_rfport_mo(node_type, synced_nodes,
                                                                                 rfport_fdn_list)

                if nodes_found:
                    selected_nodes[node_type] = nodes_found
                    total_selected_nodes += selected_nodes[node_type].keys()
                else:
                    self.add_error_as_exception(EnvironError("Unable to select nodes of type: {0}".format(node_type)))
        # selected_nodes dictionary format
        # {RadioNode: {u'LTE40dg2ERBS00001': {'node': <BaseNodeLite LTE40dg2ERBS00001>,
        # 'node_rfport_fdn_list': [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,
        # ManagedElement=LTE40dg2ERBS00001,Equipment=1,FieldReplaceableUnit=1,RfPort=D']}},
        # ERBS: {u'netsim_LTE05ERBS00037': {'node': <BaseNodeLite netsim_LTE05ERBS00037>,
        # 'node_rfport_fdn_list': [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,
        # MeContext=netsim_LTE05ERBS00037,ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,RfPort=D']}}

        selected_nodes, final_selected_nodes = self.get_required_nodes_from_profile_selected_nodes(
            total_selected_nodes, selected_nodes)
        log.logger.debug("Total selected nodes: {0} from profile allocated nodes: {1}"
                         "".format(len(final_selected_nodes), len(nodes_list)))
        log.logger.debug("Nodes selection operation complete.")
        unused_nodes = [allocated_node for allocated_node in nodes_list
                        if allocated_node.node_id not in final_selected_nodes]

        if unused_nodes:
            log.logger.debug("Deallocating the unused nodes from {} profile".format(self.NAME))
            self.update_profile_persistence_nodes_list(unused_nodes)

        return selected_nodes

    def initialize_profile_prerequisites(self):
        """
        Initialize Profile prerequisites, e.g. create user, select relevant nodes etc

        :return: Nodes to use
        :rtype: dict
        """
        node_attributes = ["node_id", "netsim", "simulation", "primary_type", "node_name", "profiles"]
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        log.logger.debug('Trying to fetch nodes to be used')
        if nodes_list:
            try:
                self.USER = self.create_users(1, self.USER_ROLES, fail_fast=False, retry=True)[0]
            except Exception as e:
                self.add_error_as_exception(e)
            else:
                try:
                    return self.select_nodes_to_use(self.USER, nodes_list)
                except KeyError as e:
                    self.add_error_as_exception(EnvironError('{0} Node not found in ENM'.format(e.message)))
                except Exception as e:
                    self.add_error_as_exception(e)

    def execute_flow(self):
        """
        Main flow for PM_79
        """
        selected_nodes = self.initialize_profile_prerequisites()

        if selected_nodes:
            self.teardown_list.append(partial(perform_teardown_actions, self.USER, selected_nodes))
            try:
                check_and_remove_old_ulsas_in_enm(self.USER, self)
            except Exception as e:
                self.add_error_as_exception(e)
            log.logger.debug('Waiting until first scheduled time')
            self.wait_until_first_scheduled_time()
            log.logger.debug('End first scheduled time waiting')
            self.state = "RUNNING"
            while self.keep_running():
                log.logger.debug('keep waiting ')
                self.sleep_until_time()

                try:
                    self.create_and_execute_threads_ulsa(selected_nodes)
                except Exception as e:
                    self.add_error_as_exception(e)

        else:
            self.add_error_as_exception(
                EnvironError('Problems encountered while trying to select nodes for this profile - '
                             'see log file for more details'))

    def get_rfport_fdn_list_from_profile_allocated_nodes(self, nodes_list):
        """
        Get RfPort MO's fdn list from ENM.
        Filters the RfPort MO's fdn list from profile allocated nodes.

        :param nodes_list: list of profile allocated nodes
        :type nodes_list: list

        :return: rfport MO's fdn list from profile allocated nodes.
        :rtype: list
        """
        rfport_mos_fdn_list = []
        rfport_fdn_list = get_rfport_fdn_list_from_enm(self.USER)
        log.logger.debug("Number of RfPort MO's found: {0}".format(len(rfport_fdn_list)))
        for node in nodes_list:
            node_substr = "{0},".format(node.node_id)
            rfport_fdn = [fdn for fdn in rfport_fdn_list if node_substr in fdn]
            if rfport_fdn:
                rfport_mos_fdn_list.append(rfport_fdn[0])
        log.logger.debug("{0} RfPort MO's found from {1} profile allocated nodes".format(len(rfport_mos_fdn_list),
                                                                                         len(nodes_list)))
        return rfport_mos_fdn_list

    def get_required_nodes_from_profile_selected_nodes(self, total_selected_nodes, selected_nodes):
        """
        This method used to get required number of nodes(TOTAL_REQUIRED_NODES) from total selected nodes and
        unused nodes will remove from selected_nodes.

        :param total_selected_nodes: list of selected nodes names
        :type total_selected_nodes: list
        :param selected_nodes: dictionary of selected nodes
                                {"ERBS:{"node1":{"node": nodeobject, "node_rfport_fdn_list":["rfport1"]}},
                                "RadioNode:{"node2":{"node": nodeobject, "node_rfport_fdn_list":["rfport2"]}}}
        :type selected_nodes: dict

        :return: tuple of final_selected_nodes, selected_nodes
        :rtype: tuple
        """
        final_selected_nodes = []
        if total_selected_nodes and selected_nodes:
            shuffle(total_selected_nodes)  # change the position of the ERBS, Radionodes in total_selected_nodes list
            final_selected_nodes = total_selected_nodes[:self.TOTAL_REQUIRED_NODES]  # it takes 500 nodes from total_selected_nodes
            for node_type in selected_nodes.keys():  # Removing unused ERBS/RadioNode nodes from selected_nodes dictionary
                for node in selected_nodes[node_type].items():
                    # check each node with final_selected_nodes list, whether node not existed on final_selected_nodes
                    if node[0] not in final_selected_nodes:
                        del selected_nodes[node_type][node[0]]  # if node doesn't exist then node deleted from selected_nodes dictionary

        return selected_nodes, final_selected_nodes
