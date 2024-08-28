import datetime
import json
import re
import time
from functools import partial

from enmutils.lib import log
from enmutils.lib.enm_node import get_enm_network_element_sync_states
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.enm_deployment import get_fdn_list_from_enm, get_pm_function_enabled_nodes
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.pm_flows.pmprofile import PmProfile

GET_ALL_ULSA_FDNS_URL = "pmul-service/rest/dps/node/{node_name}/ulsa/"
START_ULSA_SAMPLING = "pmul-service/rest/command/start"
STOP_ULSA_SAMPLING = ("pmul-service/rest/command/stop/node/{node_name}/ulsa/0/port/{rfport_fdn}/"
                      "samplingType/CONTINUOUS")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

SAMPLINGTIMEOUT_SECS = 6 * 60 * 60  # 6 hours, sampling will auto-stop after this time has elapsed
SAMPLINGINTERVAL_SECS = 2
CENTERFREQUENCY_KHZ = 678175
DISPLAYEDBANDWIDTH_KHZ = 100
RESOLUTIONDBANDWIDTH_KHZ = 100


def create_ulsa_mo_objects(user, node, fdn_of_ulsa_parent_mo, ulsa_instances_to_be_created):
    """
    Create UlSpectrumAnalyzer MO objects for the given node.

    :param user: User object. User that runs the cmcli commands.
    :type user: enmutils.lib.enm_user_2.User
    :param node: Node object. Node in which the UlSA MO objects will be created for each node.
    :type node: enmutils.lib.enm_node.BaseLiteNode
    :param fdn_of_ulsa_parent_mo: FDN of ULSA Parent MO
    :type fdn_of_ulsa_parent_mo: str
    :param ulsa_instances_to_be_created: List of ULSA instances to be created
    :type ulsa_instances_to_be_created: list

    :raises EnmApplicationError: if ENM doesnt give expected output

    """
    log.logger.debug("User {0} is creating UlSpectrumAnalyzer MO's on node: {1}"
                     .format(user.username, node.node_name))

    for ulsa_instance in ulsa_instances_to_be_created:

        ulsa_fdn = "{0},UlSpectrumAnalyzer={1}".format(fdn_of_ulsa_parent_mo, ulsa_instance)
        cmd = "cmedit create {0} UlSpectrumAnalyzerId={1}".format(ulsa_fdn, ulsa_instance)
        try:
            response = user.enm_execute(cmd)
            enm_output = response.get_output()
        except Exception as e:
            raise EnmApplicationError("ENM command execution unsuccessful:'{0}' - {1}".format(cmd, str(e)))

        if "1 instance(s)" not in " ".join(enm_output):
            raise EnmApplicationError("Problem encountered while trying to create MO's on ENM via command "
                                      "'{0}' - {1}".format(cmd, enm_output))

        log.logger.debug("UlSpectrumAnalyzer with ID {0} created: {1}".format(ulsa_instance, enm_output))


def delete_ulsa_mo_objects(user, ulsa_fdn):
    """
    Delete the UlSpectrumAnalyzer MO objects created by this profile on a given node.

    :param user: User object. User that runs the cmcli commands.
    :type user: enmutils.lib.enm_user_2.User
    :param ulsa_fdn: FDN of ULSA MO
    :type ulsa_fdn: str

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    log.logger.debug("User {0} is deleting UlSpectrumAnalyzer MO: {1}".format(user.username, ulsa_fdn))

    cmd = "cmedit delete {0}".format(ulsa_fdn)
    try:
        response = user.enm_execute(cmd)
        enm_output = response.get_output()
    except Exception as e:
        raise EnmApplicationError("ENM command execution unsuccessful:'{0}' - {1}".format(cmd, str(e)))

    if "1 instance(s) deleted" not in " ".join(enm_output):
        raise EnmApplicationError("Problem encountered while trying to delete MO's on ENM via command "
                                  "'{0}' - {1}".format(cmd, enm_output))

    log.logger.debug("UlSpectrumAnalyzer MO was deleted: {0} - {1}".format(ulsa_fdn, enm_output))


def start_ulsa_uplink_measurement(node_info, user):
    """
    Start Continuous Uplink Spectrum Sampling on a node

    :param node_info: Details of Node where sampling will be started
    :type node_info: tuple
    :param user: User that will execute the commands to start the UlSA measurements.
    :type user: enmutils.lib.enm_user_2.User

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    node_name = node_info[0]

    log.logger.info("User {0} is starting Continuous Uplink Spectrum Sampling on node {1}"
                    .format(user.username, node_name))
    json_data = {"nodeId": node_name,
                 "ulsaMoName": "0",
                 "ulsaStartCenterFrequencyParameter": CENTERFREQUENCY_KHZ,
                 "ulsaStartDisplayedBandwidthParameter": DISPLAYEDBANDWIDTH_KHZ,
                 "ulsaStartPortParameter": node_info[1],
                 "ulsaStartResolutionBandwidthParameter": RESOLUTIONDBANDWIDTH_KHZ,
                 "ulsaStartSamplingIntervalParameter": SAMPLINGINTERVAL_SECS,
                 "ulsaStartSamplingTimeoutParameter": SAMPLINGTIMEOUT_SECS,
                 "ulsaStartSamplingTypeParameter": "CONTINUOUS_SAMPLING"}
    log.logger.debug("Data to be passed with request: {0}".format(json_data))

    response = user.post(START_ULSA_SAMPLING, data=json.dumps(json_data), headers=HEADERS)
    raise_for_status(response, message_prefix='Could not start uplink sampling for node {0}'.format(node_name))

    log.logger.debug("Result of starting 'Continuous Uplink Spectrum Sampling': '{0}'".format(response.content))
    if "triggeredat" not in response.content:
        log.logger.debug("Unsuccessful result - expecting 'triggeredat' key in responce from ENM")
        raise EnmApplicationError("Failures occured while starting Uplink sampling on node {0}".format(node_name))

    log.logger.info("Operation to start Continuous Uplink Spectrum Sampling on node {0} has completed successfuly"
                    .format(node_name))


def stop_ulsa_uplink_measurement(node_info, user):
    """
    Stop Continuous Uplink Spectrum Sampling on a node

    :param node_info: Details of Node where sampling will be started
    :type node_info: tuple
    :param user: User that will execute the ENM commands
    :type user: enmutils.lib.enm_user_2.User

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    node_name = node_info[0]

    log.logger.info("User {0} is stopping Continuous Uplink Spectrum Sampling on node {1}"
                    .format(user.username, node_name))
    log.logger.debug("Node_information: {0}".format(node_info))

    stop_sampling = STOP_ULSA_SAMPLING.format(node_name=node_name, rfport_fdn=node_info[1])
    response = user.put(stop_sampling)

    log.logger.debug("Result of stop operation: '{0}'".format(response.content))

    message = "" if response.json().get('jobState') == 'STOPPED' else "not "
    log.logger.debug("Sampling {message}stopped on node {node_name} (i.e. jobState==STOPPED in response when job is "
                     "stopped)".format(message=message, node_name=node_name))


def extract_rfport_ldn_from_fdn(rfport_fdn):
    """
    Format the given FDN cli output line to get the node name and the LDN value.

    :param rfport_fdn: FQDN (Fully Qualified Domain name) of RfPort MO
    :type rfport_fdn: str

    :return: LDN (Local Domain Name) of RfPort MO
    :rtype: str
    :raises EnvironError: if FDN doesnt contain ManagedElement
    """

    match = re.search('(ManagedElement.*)', rfport_fdn)
    if match:
        return match.group(1)
    else:
        raise EnvironError("ManagedElement not found in RfPort MO - unexpected situation: '{0}'".format(rfport_fdn))


def check_and_remove_old_ulsas_in_enm(user, profile):
    """
    check and remove old ulsa's in enm based on profile name.
    :param user: User object. User that runs the cmcli commands.
    :type user: enmutils.lib.enm_user_2.User
    :param profile: Profile instance.
    :type profile: PM_52/PM_79
    """
    list_of_ulsas = get_ulsas_from_enm_based_on_profile_name(user, profile.NAME)
    log.logger.debug("{0} old FDN of ulsa's existed in enm for {1} profile".format(len(list_of_ulsas), profile.NAME))
    for ulsa in list_of_ulsas:
        try:
            delete_ulsa_mo_objects(user, ulsa_fdn=ulsa)
        except Exception as e:
            profile.add_error_as_exception(e)


def get_current_list_of_ulsa_mos_for_node(user, node):
    """
    Query ENM via REST call to get list of ULSA MO's for a particular node

    :param user: User that will execute the ENM commands
    :type user: enmutils.lib.enm_user_2.User
    :param node: Node object. Node in which the UlSA MO objects will be created for each node.
    :type node: enmutils.lib.enm_node.BaseLiteNode
    :return: List of FDN's
    :rtype: list
    :raises EnmApplicationError: if ENM doesnt give expected output
    """

    log.logger.debug("User {0} is querying ENM to get UlSpectrumAnalyzer MO's that exist on node {1}"
                     .format(user.username, node.node_name))

    response = user.get(GET_ALL_ULSA_FDNS_URL.format(node_name=node.node_id))
    raise_for_status(response, message_prefix='Could not get the ULSA details for node {0}'.format(node.node_id))

    ulsa_data = response.json()

    ulsa_mo_list = []
    for ulsa_id in ulsa_data:
        if "fdn" in ulsa_data[ulsa_id]:
            ulsa_mo_list.append(ulsa_data[ulsa_id]["fdn"])

    return ulsa_mo_list


def get_fdn_of_ulsa_parent(user, node):
    """
    Get the FDN of the UlSpectrumAnalyzer Parent MO for a given Node

    :param user: User object. User that runs the cmcli commands.
    :type user: enmutils.lib.enm_user_2.User
    :param node: Node object. Node in which the UlSA MO objects will be created for each node.
    :type node: enmutils.lib.enm_node.BaseLiteNode
    :return: ULSA Parent MO
    :rtype: str

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    mo_name = "NodeManagementFunction" if "ERBS" in node.primary_type else "NodeSupport"

    log.logger.debug("User {0} is attempting to get FDN of MO {1} for {2} node {3} "
                     .format(user.username, mo_name, node.primary_type, node.node_name))

    cmd = "cmedit get {0} {1}".format(node.node_id, mo_name)
    try:
        response = user.enm_execute(cmd)
        enm_output = response.get_output()
    except Exception as e:
        raise EnmApplicationError("ENM command execution unsuccessful:'{0}' - {1}".format(cmd, str(e)))

    log.logger.debug("ENM output: ..{}..".format(enm_output))
    ulspectrumanalyzer_parent_mo_fdn = None

    for line in enm_output:
        if "FDN : " in line:
            ulspectrumanalyzer_parent_mo_fdn = line.strip('FDN : ')
            break

    if not ulspectrumanalyzer_parent_mo_fdn:
        raise EnmApplicationError("Required MO is missing: {0} - profile cannot continue".format(mo_name))

    return ulspectrumanalyzer_parent_mo_fdn


def get_rfport_fdn_list_from_enm(user):
    """
    Get the list of RfPort FDN's from ENM

    :param user: User that will execute the ENM commands
    :type user: enmutils.lib.enm_user_2.User
    :return: List of RfPort FDN's found on ENM
    :rtype: list
    :raises EnmApplicationError: if ENM doesnt give expected output
    :raises EnvironError: if no RfPort MO's are found on ENM
    """
    level = 0
    status = False
    log.logger.debug("Fetching list of all RfPort MO's on ENM")
    cmd = "cmedit get * RfPort"

    while not status and level <= 2:
        response = user.enm_execute(cmd)
        enm_output = response.get_output()
        if "instance(s)" in " ".join(enm_output):
            status = True
        if not status:
            time.sleep(120)
            level += 1
            log.logger.debug("Error occured while getting rfport MO(s), sleeping for 120s before retrying")

    if "instance(s)" not in " ".join(enm_output):
        raise EnmApplicationError("Problem encountered while trying to perform ENM command '{0}' - {1}"
                                  .format(cmd, enm_output))

    rfport_fdn_list = []
    for line in enm_output:
        match = re.search("FDN : (.*)", line)
        if match:
            rfport_fdn_list.append(match.group(1))

    if not rfport_fdn_list:
        raise EnvironError("No RfPort MO's found on ENM - cannot proceed")

    return rfport_fdn_list


def get_ulsas_from_enm_based_on_profile_name(user, profile_name):
    """
    Get the FDN of the UlSpectrumAnalyzer from enm based on profile name.

    :param user: User object. User that runs the cmcli commands.
    :type user: enmutils.lib.enm_user_2.User
    :param profile_name: Name of the profile.
    :type profile_name: str
    :return: list of all FDN of the UlSpectrumAnalyzers
    :rtype: list

    :raises EnmApplicationError: if ENM doesnt give expected output
    """
    log.logger.debug("Fetching list of all FDN of the UlSpectrumAnalyzers from ENM")

    cmd = "cmedit get * UlSpectrumAnalyzer={profile_name}*"

    try:
        response = user.enm_execute(cmd.format(profile_name=profile_name))
        enm_output = response.get_output()
    except Exception as e:
        raise EnmApplicationError("ENM command execution unsuccessful: '{0}' - {1}".format(cmd, str(e)))

    if "instance(s)" not in " ".join(enm_output):
        raise EnmApplicationError("Problem encountered while trying to perform ENM command '{0}' - {1}"
                                  .format(cmd, enm_output))

    response_string = "\n".join(enm_output)
    pattern = re.compile(r'{0}'.format("FDN : (.*)"))
    list_of_ulsa = pattern.findall(response_string)

    if not list_of_ulsa:
        log.logger.debug("FDN of ulsa's do not exist for {0} profile".format(profile_name))

    return list_of_ulsa


def perform_teardown_actions(user, selected_nodes, profile):
    """
    Performs the Teardown actions, i.e. stop the ULSA sampling on all nodes

    :param user: User object. User that runs the CM CLI commands.
    :type user: enmutils.lib.enm_user_2.User
    :param selected_nodes: list of tuples of nodes & RfPort MO's
    :type selected_nodes: list
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile_flows.pm_flows.pm52profile.Pm52Profile`
    """
    log.logger.debug("Performing teardown action: Stop ULSA sampling")
    profile.create_and_execute_threads(selected_nodes, len(selected_nodes),
                                       func_ref=stop_ulsa_uplink_measurement, args=[user])


def check_node_existed_in_used_netsims(node, used_netsims):
    """
    PM_52 profile selects the 2 nodes for every netsim box.
    This function verifies the 2 nodes are used or not for netsim box.

    :param node: Node object
    :type node: enmutils.lib.enm_node.BaseLiteNode
    :param used_netsims: list of netsims being used
    :type used_netsims: list

    :return: True, if 2 nodes are not used from one netsim.
             False, if already 2 nodes are used from one netsim.
    :rtype: bool
    """
    node_selected_status = False
    if (node.netsim not in used_netsims) or (len([node_netsim for node_netsim in used_netsims
                                                  if node.netsim == node_netsim]) < 2):
        node_selected_status = True
    return node_selected_status


def get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes(user, synced_pm_enabled_nodes):
    """
    Get RfPort MO's fdn list and ULSA MO's fdn list from ENM.
    Filters the RfPort MO's fdn list and ULSA MO's fdn list from pm enabled nodes (profile allocated nodes)

    :param user: User that will execute the ENM commands
    :type user: enmutils.lib.enm_user_2.User
    :param synced_pm_enabled_nodes: list synced pm enabled nodes (profile allocated nodes)
    :type synced_pm_enabled_nodes: list

    :return: tuple of rfport MO's fdn list and ULSA MO's fdn list
    :rtype: tuple
    """
    rfport_mos_fdn_list = []
    ulsa_mos_fdn_list = []
    rfport_fdn_list = get_fdn_list_from_enm(user, "RfPort")
    ulsa_fdn_list = get_fdn_list_from_enm(user, "UlSpectrumAnalyzer")

    for node in synced_pm_enabled_nodes:
        node_substr = "{0},".format(node.node_id)
        rfport_fdn = [fdn for fdn in rfport_fdn_list if node_substr in fdn]
        if rfport_fdn:
            rfport_mos_fdn_list.append(rfport_fdn[0])
        ulsa_fdn = [fdn for fdn in ulsa_fdn_list if node_substr in fdn]
        if ulsa_fdn:
            ulsa_mos_fdn_list.append(ulsa_fdn[0])

    log.logger.debug("{0} RfPort MO's found from {1} synced pm enabled nodes".format(len(rfport_mos_fdn_list),
                                                                                     len(synced_pm_enabled_nodes)))
    log.logger.debug("{0} ULSA MO's found from {1} synced pm enabled nodes".format(len(ulsa_mos_fdn_list),
                                                                                   len(synced_pm_enabled_nodes)))
    return rfport_mos_fdn_list, ulsa_mos_fdn_list


class Pm52Profile(PmProfile, GenericFlow):
    USER = None
    USER_ROLES = []
    NODES_TO_FIND = {}
    SCHEDULED_TIMES_STRINGS = []

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
        rfport_fdn_list = get_rfport_fdn_list_from_enm(user)
        log.logger.debug("Number of RfPort MO's found: {0}".format(len(rfport_fdn_list)))

        log.logger.debug("Get list of all synchronized nodes in ENM")
        enm_node_sync_states = get_enm_network_element_sync_states(user)

        log.logger.debug("Exclude non-synchronized nodes from all nodes allocated to profile at startup")
        synced_nodes = [node for node in nodes_list if enm_node_sync_states[node.node_id] == "SYNCHRONIZED"]

        log.logger.debug("Exclude nodes that dont have RfPort MO's from all synced nodes")
        for node_type in self.NODES_TO_FIND:
            nodes_found = self.select_nodes_from_pool_that_contain_rfport_mo(node_type, synced_nodes, rfport_fdn_list)

            if nodes_found:
                selected_nodes[node_type] = nodes_found
                total_selected_nodes += selected_nodes[node_type].keys()
            else:
                self.add_error_as_exception(EnvironError("Unable to select nodes of type: {0}".format(node_type)))

        if selected_nodes:
            log.logger.debug("Create ULSA MO's on selected nodes if necessary")
            selected_nodes = self.update_nodes_info_with_ulsa_mos(user, selected_nodes)

        log.logger.debug("Nodes selection operation complete. Selected Node information: {0}".format(selected_nodes))
        unused_nodes = [allocated_node for allocated_node in nodes_list
                        if allocated_node.node_id not in total_selected_nodes]

        if unused_nodes:
            log.logger.debug("Deallocating the unused nodes from {0} profile".format(self.NAME))
            self.update_profile_persistence_nodes_list(unused_nodes)

        return selected_nodes

    def select_nodes(self, synced_pm_enabled_nodes, rfport_fdn_list, ulsa_fdn_list):
        """
        Selecting allocated nodes that are synchronized and contain RfPort & UlSpectrumAnalyzer MO's"

        :param synced_pm_enabled_nodes: List of synced pm enabled Node objects allocated to profile
        :type synced_pm_enabled_nodes: list
        :param rfport_fdn_list: list of RfPort MO's on ENM
        :type rfport_fdn_list: list
        :param ulsa_fdn_list: list of UlSpectrumAnalyzer MO's on ENM
        :type ulsa_fdn_list: list

        :return: list of tuples of the form (node_id, RfPort fdn)
        :rtype: list
        """
        nodes_to_find = getattr(self, "NODES_TO_FIND")
        log.logger.debug("Selecting required number of allocated nodes: {0}".format(nodes_to_find))

        allocated_nodes_per_type = generate_basic_dictionary_from_list_of_objects(synced_pm_enabled_nodes,
                                                                                  "primary_type")

        log.logger.debug("Filtering {0} synchronized nodes (with PM enabled) to find nodes having  "
                         "RfPort & UlSpectrumAnalyzer MO's. Note: only 2 nodes will be selected per "
                         "Netsim host in order to limit CPU usage"
                         .format(len(synced_pm_enabled_nodes)))
        selected_nodes = []
        used_netsims = []
        for node_type in allocated_nodes_per_type.keys():
            log.logger.debug("Allocated {0} nodes: {1}".format(node_type, len(allocated_nodes_per_type[node_type])))
            number_of_nodes_selected = 0

            for node in allocated_nodes_per_type[node_type]:
                rfport_fdn = self.get_rfport_for_node(node, used_netsims[:], rfport_fdn_list, ulsa_fdn_list)
                if rfport_fdn:
                    node_info = (node.node_id, rfport_fdn)
                    selected_nodes.append(node_info)
                    used_netsims.append(node.netsim)
                    number_of_nodes_selected += 1
                    log.logger.debug("{0} node {1} selected from {2}".format(node_type, node.node_id, node.netsim))

                if number_of_nodes_selected == nodes_to_find[node_type]:
                    break

            if number_of_nodes_selected != nodes_to_find[node_type]:
                self.add_error_as_exception(
                    EnvironError("Profile could not select required number of {0} nodes ({1}/{2} selected)"
                                 .format(node_type, number_of_nodes_selected, nodes_to_find[node_type])))

        return selected_nodes

    @staticmethod
    def get_rfport_for_node(node, used_netsims, rfport_fdn_list, ulsa_fdn_list):
        """
        Get RfPort FDN for supplied node

        :param node: Node object
        :type node: enmutils.lib.enm_node.BaseLiteNode
        :param used_netsims: list of netsims being used
        :type used_netsims: list
        :param rfport_fdn_list: list of RfPort MO's on ENM
        :type rfport_fdn_list: list
        :param ulsa_fdn_list: list of UlSpectrumAnalyzer MO's on ENM
        :type ulsa_fdn_list: list

        :return: RfPort FDN
        :rtype: str
        """
        node_substr = "{0},".format(node.node_id)
        node_used_netsim_status = check_node_existed_in_used_netsims(node, used_netsims)
        if (node_used_netsim_status and
                any(node_substr in _ for _ in rfport_fdn_list) and
                any(node_substr in _ for _ in ulsa_fdn_list)):
            rfport_fdn = [fdn for fdn in rfport_fdn_list if node_substr in fdn][0]  # Only 1 RfPort needed
            return rfport_fdn

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

        log.logger.debug("Picking {0} {1} Node(s) from pool having RfPort MO ..."
                         .format(self.NODES_TO_FIND[node_type], node_type))

        nodes_with_rfport_mos = {}

        possible_nodes = [node for node in nodes if node.primary_type == node_type]
        for node in possible_nodes:
            list_of_rfport_fdns = [fdn for fdn in rfport_fdn_list if "{0},".format(node.node_id) in fdn]

            if list_of_rfport_fdns:
                if len(nodes_with_rfport_mos.keys()) < self.NODES_TO_FIND[node_type]:
                    nodes_with_rfport_mos[node.node_id] = {'node': node, 'node_rfport_fdn_list': list_of_rfport_fdns}
                else:
                    break

        if len(nodes_with_rfport_mos.keys()) < self.NODES_TO_FIND[node_type]:
            self.add_error_as_exception(EnvironError("Unable to select required number of {0} {1} nodes containing "
                                                     "RfPort MO".format(self.NODES_TO_FIND[node_type], node_type)))

        return nodes_with_rfport_mos

    def update_nodes_info_with_ulsa_mos(self, user, nodes):
        """
        Update Node information with FDN's of any ULSA MO's that exist on the node

        :param user: User that will execute the ENM commands
        :type user: enmutils.lib.enm_user_2.User
        :param nodes: dictionary of nodes, with rfport info
        :type nodes: dict
        :return: Dictionary of Nodes with updated ULSA MO info on them
        :rtype: dict
        """
        log.logger.debug("Fetching existing ULSA MO information for selected nodes")
        for node_type in nodes:
            for node_name in nodes[node_type]:
                node_primary_type = nodes[node_type][node_name]['node'].primary_type
                required_number_of_ulsa_instances = 1 if "RadioNode" in node_primary_type else 4

                current_list_of_ulsa_mos = get_current_list_of_ulsa_mos_for_node(user,
                                                                                 nodes[node_type][node_name]['node'])
                log.logger.debug("ULSA MO's listed for node {0}:  {1}".format(node_name, current_list_of_ulsa_mos))

                if len(current_list_of_ulsa_mos) < required_number_of_ulsa_instances:
                    log.logger.debug("Extra ULSA MO's need to be created on {0} node {1}".format(node_type, node_name))
                    fdn_of_ulsa_parent_mo = get_fdn_of_ulsa_parent(user, nodes[node_type][node_name]['node'])

                    number_of_ulsa_instances_to_be_created = (required_number_of_ulsa_instances -
                                                              len(current_list_of_ulsa_mos))

                    ulsa_instances_to_be_created = []
                    for instance in xrange(number_of_ulsa_instances_to_be_created):
                        ulsa_instances_to_be_created.append("{0}_ULSA_{1}".format(self.NAME, instance))

                    create_ulsa_mo_objects(user, nodes[node_type][node_name]['node'], fdn_of_ulsa_parent_mo,
                                           ulsa_instances_to_be_created)

                    current_list_of_ulsa_mos = get_current_list_of_ulsa_mos_for_node(
                        user, nodes[node_type][node_name]['node'])

                    log.logger.debug("ULSA MO's listed for node: {0} is {1}"
                                     .format(node_name, current_list_of_ulsa_mos))

                nodes[node_type][node_name]['ulsa_mo_list'] = current_list_of_ulsa_mos

        return nodes

    def initialize_profile_prerequisites(self):
        """
        Initialize Profile prerequisites, e.g. create user, select relevant nodes etc

        :return: Nodes to use
        :rtype: dict
        """
        node_attributes = ["node_id", "netsim", "simulation", "primary_type", "node_name", "profiles"]
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
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

    def filter_synced_pm_enabled_nodes(self, nodes, user):
        """
        To get the Synced and pm enabled nodes.

        :type nodes: list
        :param nodes: List of `enm_node.Node` to get PM Function enabled or not
        :param user: User object
        :type user: enm_user_2.User

        :rtype: list
        :return: List of synced pm enabled nodes
        :raises EnvironError: if Synced nodes are not available, PM Function is not enabled on all nodes
        """
        synced_nodes, _ = check_sync_and_remove(nodes, user)
        if synced_nodes:
            synced_pm_enabled_nodes, _ = get_pm_function_enabled_nodes(synced_nodes, user)
            if not synced_pm_enabled_nodes:
                raise EnvironError("PM is not enabled on any nodes allocated to the profile")
            return synced_pm_enabled_nodes
        else:
            raise EnvironError("Synced nodes are not available")

    def get_unused_nodes_and_deallocate_from_profile(self, allocated_nodes, used_nodes):
        """
        Get unused nodes and deallocate that nodes from profile.

        :type allocated_nodes: list
        :param allocated_nodes: List of profile allocated nodes (`enm_node.Node`)
        :type used_nodes: list
        :param used_nodes: List of profile used nodes nodes (`enm_node.Node`)

        """
        unused_nodes = [node for node in allocated_nodes if node.node_id not in [_[0] for _ in used_nodes]]
        if unused_nodes:
            log.logger.debug("Deallocating the unused nodes from {0} profile".format(self.NAME))
            self.update_profile_persistence_nodes_list(unused_nodes)

    def filter_profile_nodes(self, user):
        """
        Filter profile nodes based on requirements etc

        :param user: User object
        :type user: enm_user_2.User

        :return: Nodes to use
        :rtype: list
        """
        node_attributes = ["node_id", "netsim", "primary_type", "profiles"]
        allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        if allocated_nodes:
            try:
                synced_pm_enabled_nodes = self.filter_synced_pm_enabled_nodes(allocated_nodes, user)
                synced_rfport_fdn_list, synced_ulsa_fdn_list = get_rfport_fdn_and_ulsa_fdn_list_from_synced_pm_nodes(
                    user, synced_pm_enabled_nodes)
                selected_nodes = self.select_nodes(synced_pm_enabled_nodes, synced_rfport_fdn_list,
                                                   synced_ulsa_fdn_list)
                self.get_unused_nodes_and_deallocate_from_profile(allocated_nodes, selected_nodes)

                return selected_nodes

            except Exception as e:
                self.add_error_as_exception(e)

    def wait_until_first_scheduled_time(self):
        """
        Wait until just before (i.e. time_gap = 2 min) the first scheduled time is reached

        ULSA Sampling is meant to start at the 1st scheduled time and stop at the 2nd scheduled time.
        If the profile is started after after the 1st scheduled time, then the profile must wait until the next
        occurrence of the 1st scheduled time.
        e.g. If the 1st scheduled time is 00:00 with the 2nd scheduled time set to 12:00, then if the profile is
        started at 10:00, then the sampling will only start when the time reaches 00:00, not 12:00
        """
        log.logger.debug("Checking to see if profile needs to wait till next scheduled time")
        time_gap = 30
        time_now = datetime.datetime.now()
        start_time = datetime.datetime.strptime(self.SCHEDULED_TIMES_STRINGS[0], "%H:%M:%S")

        expected_start_time_today = start_time.replace(
            year=time_now.year, month=time_now.month, day=time_now.day,
            hour=start_time.hour, minute=start_time.minute, second=start_time.second)

        if time_now > expected_start_time_today:
            time_tomorrow = time_now + datetime.timedelta(days=1)

            first_scheduled_time_tomorrow = start_time.replace(
                year=time_tomorrow.year, month=time_tomorrow.month, day=time_tomorrow.day,
                hour=start_time.hour, minute=start_time.minute, second=start_time.second)

            number_of_seconds_until_first_scheduled_time = int((first_scheduled_time_tomorrow - time_now)
                                                               .total_seconds())

            time_to_sleep = number_of_seconds_until_first_scheduled_time - time_gap
            self.state = "SLEEPING"
            log.logger.debug("Sleeping {0}s to ensure that the ULSA sampling will start at the scheduled time {1}"
                             .format(time_to_sleep, self.SCHEDULED_TIMES_STRINGS[0]))
            time.sleep(number_of_seconds_until_first_scheduled_time - time_gap)

    def execute_flow(self):
        """
        Main flow for PM_52
        """
        user_roles = getattr(self, "USER_ROLES")
        user = self.create_profile_users(1, user_roles)[0]
        selected_nodes = self.filter_profile_nodes(user)

        if selected_nodes:

            self.state = "RUNNING"
            try:
                check_and_remove_old_ulsas_in_enm(user, self)
            except Exception as e:
                self.add_error_as_exception(e)
            teardown_populated = False
            while self.keep_running():
                self.sleep_until_time()

                self.create_and_execute_threads(selected_nodes, len(selected_nodes),
                                                func_ref=start_ulsa_uplink_measurement, args=[user])

                if not teardown_populated:
                    self.teardown_list.append(partial(perform_teardown_actions, user, selected_nodes, self))
                    teardown_populated = True

        else:
            self.add_error_as_exception(
                EnvironError('Problems encountered while trying to select nodes for this profile - '
                             'see log file for more details'))
