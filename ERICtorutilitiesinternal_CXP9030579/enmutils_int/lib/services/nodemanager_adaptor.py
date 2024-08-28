import imp
import re

from retrying import retry

from enmutils.lib import log, enm_node, config
from enmutils.lib.exceptions import NoNodesAvailable, EnvironError
from enmutils_int.lib import common_utils
from enmutils_int.lib.enm_mo import EnmMo
from enmutils_int.lib.services import service_adaptor, service_registry
from enmutils_int.lib.services.service_adaptor import print_service_operation_message
from enmutils_int.lib.services.service_values import GET_METHOD, POST_METHOD
from enmutils_int.lib.services.usermanager_adaptor import BasicUser
from enmutils_int.lib.workload_network_manager import InputData

SERVICE_NAME = "nodemanager"

LIST_NODES_URL = "nodes/list"
ADD_NODES_URL = "nodes/add"
REMOVE_NODES_URL = "nodes/remove"
RESET_NODES_URL = "nodes/reset"
UPDATE_NODE_URL = ""
ALLOCATE_NODES_URL = "nodes/allocate"
DEALLOCATE_NODES_URL = "nodes/deallocate"
UPDATE_POIDS_URL = "nodes/update_poids"
UPDATE_NODES_CACHE = "nodes/update_cache_on_request"
MAX_NODES_COUNT_PER_REQUEST = 1000
RETRY_TIME_SECS = 10


def can_service_be_used(profile=None):
    """
    Determine if service can be used

    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    :return: Boolean to indicate if service can be used or not
    :rtype: bool
    """
    priority = profile.priority if profile else None
    service_can_be_used = service_registry.can_service_be_used(SERVICE_NAME, priority)
    log.logger.debug("Service {0} can be used: {1}".format(SERVICE_NAME, service_can_be_used))
    return service_can_be_used


def add_nodes(argument_dict):
    """
    Add nodes to the workload pool

    :param argument_dict: Command line arguments received from the workload tool
    :type argument_dict: dict
    """
    try:
        sanitize_values(argument_dict)
    except ValueError as e:
        log.logger.info(str(e))
        return
    file_name = argument_dict.get("IDENTIFIER")
    node_range = argument_dict.get("RANGE")
    log.logger.debug("Starting add nodes operation.")
    json_data = {"file_name": file_name, "node_range": str(node_range)}
    print_service_operation_message(send_request_to_service(POST_METHOD, ADD_NODES_URL, json_data=json_data),
                                    log.logger)


def remove_nodes(argument_dict):
    """
    Remove nodes from the workload pool

    :param argument_dict: Command line arguments received from the workload tool
    :type argument_dict: dict
    """
    try:
        sanitize_values(argument_dict)
    except ValueError as e:
        log.logger.info(str(e))
        return
    file_name = argument_dict.get("IDENTIFIER") if argument_dict.get("IDENTIFIER") else "all"
    node_range = argument_dict.get("RANGE")
    force = "true" if argument_dict.get("force") else "false"
    log.logger.debug("Starting remove nodes operation.")
    json_data = {"file_name": str(file_name), "node_range": str(node_range), "force": force}
    print_service_operation_message(send_request_to_service(POST_METHOD, REMOVE_NODES_URL, json_data=json_data),
                                    log.logger)


def reset_nodes(reset_network_values=False, no_ansi=False):
    """
    Reset nodes in the workload pool

    :param reset_network_values: Boolean indicating if the persisted network values should be removed
    :type reset_network_values: bool
    :param no_ansi: Boolean indicating if colour logging should be disabled
    :type no_ansi: bool
    """
    log.logger.debug("Starting reset nodes operation.")
    json_data = {'reset_network_values': reset_network_values, 'no_ansi': no_ansi}
    print_service_operation_message(send_request_to_service(POST_METHOD, RESET_NODES_URL, json_data=json_data),
                                    log.logger)


def update_poids():
    """
    Update Nodes with POID information
    """
    service_adaptor.validate_response(send_request_to_service(POST_METHOD, UPDATE_POIDS_URL))


def sanitize_values(argument_dict):
    """
    Validate the supplied command lines arguments to ensure they match str["file_name"], str["range"]|None

    :param argument_dict: Command line arguments received from the workload tool
    :type argument_dict: dict
    :raises ValueError: if the supplied values are invalid
    """
    key, value = None, None
    if not argument_dict.get("IDENTIFIER"):
        key, value = "IDENTIFIER", argument_dict.get("IDENTIFIER")

    elif (argument_dict.get("RANGE") and not all(_.strip().isdigit() for _ in argument_dict.get("RANGE").split("-")) or
          argument_dict.get("RANGE") and len(argument_dict.get("RANGE").split("-")) > 2):
        key, value = "RANGE", argument_dict.get("RANGE")
    if key:
        raise ValueError("Workload pool operation failed, invalid argument(s) supplied:: [{0}: {1}]".format(key, value))


@retry(retry_on_exception=lambda e: isinstance(e, EnvironError), wait_fixed=RETRY_TIME_SECS * 1000)
def send_request_to_service(method, url, json_data=None, retry_request=False):
    """
    Send REST request to NodeManager service

    :param method: Method to be used
    :type method: method
    :param url: Destination URL of request
    :type url: str
    :param json_data: Optional json data to be send as part of request
    :type json_data: dict
    :param retry_request: Boolean indicating if the REST request should be retired if unsuccessful
    :type retry_request: bool

    :return: Response from Service Adaptor service
    :rtype: `requests.Response`

    :raises EnvironError: in the event that response with status code 202 is received
    """
    response = service_adaptor.send_request_to_service(method, url, SERVICE_NAME, json_data=json_data,
                                                       retry=retry_request)
    if response and response.status_code == 202:
        log.logger.debug("HTTP status code 202 received, with reason given: '{0}' "
                         "(see Workload service log for more details: {1}/{2}.log)"
                         .format(response.json().get("message"), log.SERVICES_LOG_DIR, SERVICE_NAME))
        log.logger.debug("Re-sending request in {0}s".format(RETRY_TIME_SECS))
        raise EnvironError()
    return response


def list_nodes(profile=None, match_patterns=None, node_attributes=None, json_response=False):
    """
    Query nodemanager service to get list of nodes, along with total node count in pool
        and number of nodes matched in query

    :param profile: Name of profile
    :type profile: str
    :param match_patterns: Regular expressions to match nodes with
    :type match_patterns: str
    :param node_attributes: List of Node attributes
    :type node_attributes: list
    :param json_response: Boolean to indicate format of data to be returned
    :type json_response: bool
    :return: tuple of: total number of nodes in pool, number of nodes returned in query, node data
            note: node_data could be
             1) a list of node dictionaries, or
             2) a dictionary of dictionaries of node data grouped by simulation etc
    :rtype: tuple
    """
    log.logger.debug("Fetching list of nodes via service")
    node_attributes = node_attributes or ["node_id"]
    json_data = {'profile': profile, 'match_patterns': match_patterns, 'node_attributes': node_attributes}
    response = send_request_to_service(POST_METHOD, LIST_NODES_URL, json_data=json_data)
    if response.ok:
        response_data = response.json().get('message')
        total_node_count = response_data["total_node_count"]
        node_count_from_query = response_data["node_count_from_query"]
        node_data = response_data["node_data"]

        log.logger.debug("Total nodes: {0}, Nodes in query: {1}".format(total_node_count, node_count_from_query))
        if json_response:
            return total_node_count, node_count_from_query, node_data
        else:
            return total_node_count, node_count_from_query, convert_received_data_to_nodes(node_data)

    log.logger.debug("Could not get nodes from service")
    return 0, 0, []


def get_list_of_nodes_from_service(profile=None, match_patterns=None, node_attributes=None, json_response=False):
    """
    Get the list of nodes from the nodemanager service

    :param profile: Name of profile
    :type profile: str
    :param match_patterns: Regular expressions to match nodes with
    :type match_patterns: str
    :param node_attributes: Node attributes
    :type node_attributes: list
    :param json_response: Boolean to indicate format of data to be returned
    :type json_response: bool
    :return: List of Node data
    :rtype: list
    """
    return list_nodes(profile, match_patterns, node_attributes, json_response)[2]


def allocate_nodes(profile, nodes=None):
    """
    Allocate nodes to a profile via service

    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    :param nodes: List of Node Objects
    :type nodes: list

    :raises NoNodesAvailable: if no nodes available
    """
    profile_name = getattr(profile, 'NAME')
    log.logger.debug("Starting allocation of nodes to {0} via service".format(profile_name))

    if nodes:
        node_id_list = [node.node_id for node in nodes]

        sub_lists = common_utils.chunks(node_id_list, MAX_NODES_COUNT_PER_REQUEST)
        for index, sublist in enumerate(sub_lists):
            log.logger.debug("Allocating specific nodes via batches ({0} - max {1} nodes per service request)"
                             .format(index + 1, MAX_NODES_COUNT_PER_REQUEST))
            nodes_list = ",".join(sublist)
            json_data = {'nodes': nodes_list, 'profile': profile_name}
            print_service_operation_message(send_request_to_service(
                POST_METHOD, ALLOCATE_NODES_URL, json_data=json_data), logger=log.logger)
    else:
        if str(profile_name) == 'HA_01' and nodes_preference_check() is True:
            response_data = erbs_node_pop(profile, nodes)
        else:
            json_data = {'profile': profile_name, 'nodes': nodes,
                         'profile_values': get_profile_attributes_and_values(profile_name),
                         'network_config': config.get_prop('network_config') if config.has_prop('network_config') else None}
            response_data = send_request_to_service(POST_METHOD, ALLOCATE_NODES_URL, json_data=json_data).json()

        if not response_data["success"]:
            raise NoNodesAvailable("Could not allocate nodes to {0}: {1}."
                                   .format(profile_name, response_data["message"]))
    setattr(profile, 'num_nodes', len(get_list_of_nodes_from_service(
        profile=profile_name, node_attributes=['node_id'])))
    log.logger.debug("Current profile num nodes value: [{0}]".format(profile.num_nodes))
    log.logger.debug("Completed allocation of nodes to {0}".format(profile_name))


def nodes_preference_check():
    """
    checks radio nodes available or not in the deployment

    :return: Returns true if radio nodes available else return false
    :rtype: bool
    """
    check = False
    json_data = {'profile': None, 'match_patterns': None, 'node_attributes': ['node_id']}
    response = send_request_to_service(POST_METHOD, LIST_NODES_URL, json_data=json_data)
    if response.ok:
        response_data = response.json().get('message')
        nodes_data = response_data["node_data"]
        for node in nodes_data:
            if 'dg2ERBS' in node['node_id']:
                log.logger.debug('Identified the radionode {0}'.format(node['node_id']))
                check = True
                break

    return check


def erbs_node_pop(profile, nodes):
    """
    Remove the ERBS nodes from NUM_NODES and then send the request for node allocation

    :param profile: Name of Profile
    :type profile: `enmutils_int.lib.profile.Profile`
    :param nodes: List of Node Objects
    :type nodes: list
    :return: Response from Service Adaptor service
    :rtype: `requests.Response`
    """
    profile_name = getattr(profile, 'NAME')
    json_data = {'profile': profile_name, 'nodes': nodes,
                 'profile_values': get_profile_attributes_and_values(profile_name),
                 'network_config': config.get_prop('network_config') if config.has_prop(
                     'network_config') else None}
    node_val = json_data.get('profile_values')
    node_num = node_val.get('NUM_NODES')
    node_num.pop('ERBS')
    response_data = send_request_to_service(POST_METHOD, ALLOCATE_NODES_URL, json_data=json_data).json()

    return response_data


def deallocate_nodes(profile, unused_nodes=None):
    """
    Deallocate nodes to a profile

    :param profile: Name of Profile
    :type profile: `enmutils_int.lib.profile.Profile`
    :param unused_nodes: List of unused Node objects
    :type unused_nodes: list
    """
    profile_name = getattr(profile, 'NAME')
    log.logger.debug("Starting deallocation of nodes from {0} via service".format(profile_name))

    if unused_nodes:
        node_id_list = [node.node_id for node in unused_nodes]
        sublists = common_utils.chunks(node_id_list, MAX_NODES_COUNT_PER_REQUEST)
        for index, sublist in enumerate(sublists):
            log.logger.debug("Deallocating nodes via batches ({0} - max {1} nodes per service request)"
                             .format(index + 1, MAX_NODES_COUNT_PER_REQUEST))
            nodes_list = ",".join(sublist)
            print_service_operation_message(
                send_request_to_service(POST_METHOD, DEALLOCATE_NODES_URL,
                                        json_data={'profile': profile_name, 'nodes': nodes_list}), log.logger)
    else:
        print_service_operation_message(
            send_request_to_service(POST_METHOD, DEALLOCATE_NODES_URL,
                                    json_data={'profile': profile_name, 'nodes': unused_nodes}), log.logger)

    log.logger.debug("Completed deallocation of nodes from {0}".format(profile_name))


def update_nodes_cache_on_request():
    """
    Performs refresh of nodes cache list in nodemanager service
    """
    log.logger.debug("Performing nodes cache update")
    service_adaptor.validate_response(send_request_to_service(GET_METHOD, UPDATE_NODES_CACHE))
    log.logger.debug("Completed nodes cache update")


def exchange_nodes(profile):
    """
    Exchange nodes tied to a profile

    :param profile: Name of Profile
    :type profile: `enmutils_int.lib.profile.Profile`
    """
    profile_name = profile.NAME
    log.logger.debug("Starting exchange of nodes for {0} via service".format(profile_name))
    deallocate_nodes(profile)
    allocate_nodes(profile)
    log.logger.debug("Completed exchange of nodes for {0}".format(profile_name))


def convert_received_data_to_nodes(node_data):
    """
    Convert received data from Nodemanager service to Node objects

    :param node_data: list of nodes
    :type node_data:
    :return: List of User objects
    :rtype: list
    """
    nodes = []
    for node_info in node_data:
        if "mos" in node_info.keys() and node_info.get("mos"):
            convert_dictionary_to_mos(node_info["mos"])
            tuple_str_keys(node_info["mos"])
        nodes.append(enm_node.BaseNodeLite(**node_info))

    return nodes


def convert_dictionary_to_mos(node_mo_dict):
    """
    Recursive function to convert the JSON response back to EnmMo instance(s)

    :param node_mo_dict: Dictionary or list depending on the MOs attributes supplied
    :type node_mo_dict: dict|list
    """
    if not getattr(node_mo_dict, "items", None):
        return
    for key, value in node_mo_dict.items():
        if any([val for val in value if getattr(val, 'items', None) and 'mo_id' in val.keys()]):
            node_mo_dict[key] = [EnmMo(**convert_dict_to_users(val)) for val in value]
        else:
            convert_dictionary_to_mos(value)


def convert_dict_to_users(mo_dict):
    """
    Converts the dictionary to BasicUser instance

    :param mo_dict: Dictionary containing the attributes of the supplied EnmMo instance
    :type mo_dict: dict

    :return: The supplied/updated dictionary
    :rtype: dict
    """
    user = mo_dict.get('user')
    if getattr(user, 'items', None) and 'password' in user.keys():
        mo_dict['user'] = BasicUser(**user)
    return mo_dict


def tuple_str_keys(node_mo_dict):
    """
    Convert string keys in ENM MOs back to tuples

    :param node_mo_dict: Dictionary containing the attributes of the supplied MO
    :type node_mo_dict: dict
    """
    if not getattr(node_mo_dict, "items", None):
        return
    for key, values in node_mo_dict.items():
        if "|||" in key:
            new_key = tuple(key.split('|||'))
            node_mo_dict[new_key] = values
            del node_mo_dict[key]
        tuple_str_keys(values)


def get_profile_attributes_and_values(profile_name):
    """
    Function to select the profile attributes for the supplied profile name

    :param profile_name: Name of the profile to fetch the values
    :type profile_name: str

    :return: Dictionary of the profile attributes/values
    :rtype: dict
    """
    profile_values = {}
    config_data = InputData()
    app = re.split(r'_[0-9]', profile_name.lower())[0].replace('_setup', '')
    workload_item = config_data.get_profiles_values(app, profile_name)
    if workload_item is not None:
        if config.has_prop('config-file'):
            for config_attribute, config_value in getattr(load_custom_config_values(), profile_name, {}).items():
                workload_item[config_attribute] = config_value
        for profile_attribute, profile_value in workload_item.iteritems():
            profile_values[profile_attribute] = profile_value

    return profile_values


def load_custom_config_values():
    """
    Load the custom config file if available

    :return: Returns the loaded file as module
    :rtype: module
    """
    file_path = config.get_prop('config-file')
    if file_path:
        try:
            return imp.load_source('profile_conf', file_path)
        except Exception as e:
            log.logger.debug("Unable to load configuration file, error encountered: {0}.".format(str(e)))
