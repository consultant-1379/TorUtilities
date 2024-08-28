import fnmatch
from copy import copy

from flask import Blueprint, request

from enmutils.lib import log, mutexer
from enmutils.lib.exceptions import NoNodesAvailable
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.services import nodemanager_helper_methods as helper
from enmutils_int.lib.services.custom_queue import CustomContainsQueue
from enmutils_int.lib.services.service_common_utils import (get_json_response, abort_with_message,
                                                            create_and_start_background_scheduled_job)
from enmutils_int.lib.services.service_values import URL_PREFIX

SERVICE_NAME = "nodemanager"

application_blueprint = Blueprint(SERVICE_NAME, __name__, url_prefix=URL_PREFIX)
PROFILE_ALLOCATION_QUEUE = CustomContainsQueue()


def at_startup():
    """
    Start up function to be executed when service is created
    """
    log.logger.debug("Running startup functions")
    helper.update_cached_nodes_list()
    helper.update_poid_attributes_on_pool_nodes()
    helper.retrieve_cell_information_and_apply_cell_type()
    create_and_start_background_scheduled_job(
        helper.retrieve_cell_information_and_apply_cell_type, 360, "{0}_APPLY_LTE_TYPE_SIX_HOURLY".format(
            SERVICE_NAME), log.logger)
    log.logger.debug("Startup functions complete")


def add_nodes():
    """
    Route to Add node(s) information to the workload pool

    POST /nodes/add

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    log.logger.debug("Adding nodes using values : {0}".format(request))
    request_data = request.get_json()
    node_range = None if request_data.get("node_range").encode("utf-8") == "None" else request_data.get(
        "node_range").encode("utf-8")
    try:
        range_start, range_end = helper.determine_start_and_end_range(node_range)
        added, missing_nodes = node_pool_mgr.add(request_data.get("file_name").encode("utf-8"), start=range_start,
                                                 end=range_end)

        poid_update_failures = 0
        if added:
            helper.update_cached_nodes_list()
            poid_update_failures = helper.update_poid_attributes_on_pool_nodes()
            helper.retrieve_cell_information_and_apply_cell_type(rebuild_dict=True)
        helper.update_total_node_count()
        total_missing = sum([len(nodes) for nodes in missing_nodes.itervalues()])

        summary = build_summary_message("ADDED", len(added), len(added) + total_missing,
                                        helper.update_total_node_count(update=False))
        if total_missing:
            summary += "\n{0}".format(print_failed_add_operation_summary(missing_nodes))
        if poid_update_failures:
            summary += "\nFailures occurred while trying to update nodes with POID info from ENM"
        return get_json_response(message=summary)
    except Exception as e:
        abort_with_message("Could not add nodes to the workload pool", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def remove_nodes():
    """
    Route to Remove node(s) information from the workload pool

    POST /nodes/remove?=argument_dict

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    log.logger.debug("Removing nodes using values : {0}".format(request))
    request_data = request.get_json()
    node_range = None if request_data.get("node_range").encode("utf-8") == "None" else request_data.get(
        "node_range").encode("utf-8")
    nodes_file_path = request_data.get("file_name").encode("utf-8")
    force = True if request_data.get("force").encode("utf-8") == "true" else False
    try:
        message = remove_nodes_from_pool(nodes_file_path, node_range, force)
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Could not remove nodes from the workload pool", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def convert_node_to_dictionary(node, required_node_attributes=None, profile_name=None):
    """
    Extract required attributes from node, for returning to caller

    :param node: BaseLoadNode object
    :type node: `enmutils_int.lib.load_node.BaseLoadNode`
    :param required_node_attributes: List of Node attributes required
    :type required_node_attributes: list or None
    :param profile_name: Name of the profile requesting nodes
    :type profile_name: str

    :return: Node dictionary
    :rtype: dict
    """

    node_dict = copy(node.to_dict())

    basenode_object_attributes = ["node_name", "subnetwork_str", "subnetwork_id", "mim", "snmp_security_level",
                                  "managed_element_type", "mos"]
    loadnodemixin_object_attributes = ["profiles", "available_to_profiles", "_is_exclusive", "lte_cell_type"]
    attributes_not_provided_by_to_dict = basenode_object_attributes + loadnodemixin_object_attributes

    for node_attribute in attributes_not_provided_by_to_dict:
        attribute_value = getattr(node, node_attribute)
        attribute_value = attribute_value if not isinstance(attribute_value, set) else list(attribute_value)
        if node_attribute == "mos" and attribute_value:
            if profile_name and profile_name.lower().startswith("cmimport"):
                with mutexer.mutex("mo-conversion", log_output=True, persisted=True):
                    helper.convert_mos_to_dictionary(attribute_value)
                    helper.stringify_keys(attribute_value)
            else:
                attribute_value = {}
        node_dict[node_attribute] = attribute_value

    if required_node_attributes and required_node_attributes != ["all"]:
        node_dict = {node_attribute: node_dict[node_attribute] for node_attribute in required_node_attributes}
    return node_dict


def reset_nodes():
    """
    Reset all of the nodes in to the pool to unallocated and Non-Exclusive if possible

    POST /nodes/reset

    :raises HTTPException: 404 raised if GET request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        reset_network_values = request_data.get('reset_network_values')
        no_ansi = request_data.get('no_ansi')
        return get_json_response(message=helper.reset_nodes(reset_network_values=reset_network_values, no_ansi=no_ansi))
    except Exception as e:
        abort_with_message("Could not reset all nodes in the workload pool", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def list_nodes():
    """
    Route to POST node information from the database where workload pool is stored (i.e. Redis)

    POST /nodes/list

    :raises HTTPException: 500 raised if POST request fails

    :return: dict containing node_id's and corresponding profiles assigned to node
    :rtype: dict
    """
    request_data = request.get_json()
    profile = request_data.get('profile')
    node_attributes = request_data.get('node_attributes')
    match_patterns = request_data.get('match_patterns')

    if profile and profile in PROFILE_ALLOCATION_QUEUE:
        log.logger.debug("Allocation currently ongoing for {0} - "
                         "Waiting for allocation to complete first".format(profile))
        PROFILE_ALLOCATION_QUEUE.block_until_item_removed(profile, log.logger, max_time_to_wait=1800)
        log.logger.debug("Waiting complete - proceeding to return list of nodes")

    json_response = dict()

    try:
        nodes = node_pool_mgr.cached_nodes_list
        json_response["total_node_count"] = len(nodes)

        if match_patterns:
            nodes = list_nodes_that_match_patterns(nodes, match_patterns)

        nodes = [node for node in nodes if not profile or (profile and profile.upper() in node.profiles)]
        json_response["node_count_from_query"] = len(nodes)

        json_response["node_data"] = [convert_node_to_dictionary(
            node, node_attributes, profile_name=profile) for node in nodes]

        log.logger.debug("Total nodes: {0}, Nodes in query: {1}".format(json_response["total_node_count"],
                                                                        json_response["node_count_from_query"]))
        return get_json_response(message=json_response)

    except Exception as e:
        abort_with_message("Could not locate node(s) in redis", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def allocate_nodes():
    """
    Route to allocate node information to a particular profile.

    POST /nodes/allocate

    :raises HTTPException: 500 raised if POST request fails
    :raises RuntimeError: raised if no profile name is supplied

    :return: Json response indicating if the outcome of the operation
    :rtype: dict
    """
    request_data = request.get_json()
    profile_name = request_data.get('profile')
    nodes = request_data.get('nodes')
    profile_values = request_data.get('profile_values')
    network_config = request_data.get('network_config')

    log.logger.debug("Performing node allocation for profile: {0}".format(profile_name))
    with mutexer.mutex("node-allocation", log_output=True):
        PROFILE_ALLOCATION_QUEUE.put_unique(profile_name)
        try:
            helper.perform_allocation_tasks(profile_name, nodes, profile_values=profile_values,
                                            network_config=network_config)
            return get_json_response(success=True)
        except NoNodesAvailable as e:
            return get_json_response(success=False, message="{0}".format(str(e)))
        except Exception as e:
            abort_with_message("Could not allocate nodes", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)
        finally:
            PROFILE_ALLOCATION_QUEUE.get_item(profile_name)


def deallocate_nodes():
    """
    Route to deallocate node information to a particular profile

    POST /nodes/deallocate

    :raises HTTPException: 500 raised if GET request fails
    :raises RuntimeError: raised if no profile name is supplied

    :return: Json response indicating if the outcome of the operation
    :rtype: dict
    """
    request_data = request.get_json()
    profile_name = request_data.get('profile')

    message = helper.set_deallocation_in_progress(profile_name)
    if message:
        return get_json_response(success=False, message=message, rc=202)

    unused_nodes = request_data.get('nodes')

    try:
        if not profile_name:
            raise RuntimeError("Profile name missing")
        helper.perform_deallocate_actions(profile_name, unused_nodes)
        return get_json_response(success=True)
    except Exception as e:
        abort_with_message("Could not deallocate node(s)", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)
    finally:
        helper.set_deallocation_complete()


def update_nodes_cache_on_request():
    """
    Route to refresh the nodes cache list in nodemanager service

    GET /nodes/update_cache_on_request

    :raises HTTPException: 500 raised if GET request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        log.logger.debug("Updating nodes cache list")
        helper.update_cached_nodes_list()
        log.logger.debug("Update of nodes cache list completed")
        return get_json_response(message="Success")
    except Exception as e:
        abort_with_message("Failure occurred while updating nodes cache list", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


########################
# Application Functions
########################

def list_nodes_that_match_patterns(nodes, match_patterns):
    """
    Get nodes in list whose name matches pattern.

    :param nodes: List of node objects
    :type nodes: list
    :param match_patterns: patterns to match against
    :type match_patterns: str
    :return: List of node objects
    :rtype: list

    """
    regex_nodes = []
    patterns = match_patterns.split(",")
    for node in nodes:
        if any(fnmatch.fnmatch(node.node_id, pattern) for pattern in patterns):
            regex_nodes.append(node)

    return regex_nodes


def remove_nodes_from_pool(nodes_file_path, node_range, force):
    """
    Attempts to remove the nodes present in the workload pool

    :param nodes_file_path: File path to the parsed nodes file or "all"
    :type nodes_file_path: str
    :param node_range: The range of nodes to be removed
    :type node_range: str
    :param force: Boolean indicating if the nodes pool should be forcefully removed
    :type force: bool

    :return: Message indicating the result of the remove operation.
    :rtype: str
    """
    profiles_still_using_nodes_msg = (
        "\nCould not remove all nodes from the workload pool as some profiles are still running.\n"
        "If all profiles are stopped, execute ./workload reset and retry the remove command.")
    if nodes_file_path.split("/")[-1] == "all":
        total_nodes = helper.update_total_node_count(update=False)
        result = node_pool_mgr.remove_all(force=force)
        if result:
            all_nodes_removed = "\n  All {0} nodes removed from the pool\n".format(total_nodes)
            message = all_nodes_removed
            helper.update_cached_nodes_list()
        else:
            message = profiles_still_using_nodes_msg
    else:
        range_start, range_end = helper.determine_start_and_end_range(node_range)
        removed, missing, allocated = node_pool_mgr.remove(nodes_file_path, start=range_start, end=range_end,
                                                           force=force)
        if removed:
            helper.update_cached_nodes_list()
        message = update_remove_message(removed, missing, allocated, profiles_still_using_nodes_msg)
    return message


def update_remove_message(removed, missing, allocated, still_running_msg):
    """
    Update the remove message if there are allocated or missing nodes

    :param removed: Nodes which have been successfully removed from the workload pool
    :type removed: list
    :param missing: Nodes which are not in the workload pool
    :type missing: list
    :param allocated: Nodes which are still allocated
    :type allocated: list
    :param still_running_msg: Message indicating nodes are still allocated
    :type still_running_msg: str

    :return: Updated message if not all nodes could be removed
    :rtype: str
    """
    total_nodes = sum([len(_) for _ in [removed, missing, allocated]])
    message = build_summary_message("REMOVED", len(removed), total_nodes, helper.update_total_node_count())
    if allocated:
        message += still_running_msg
    if missing:
        message += print_failed_remove_operation_summary(missing)
    return message


def build_summary_message(operation, successful_nodes, total_nodes, total_node_count):
    """
    Builds  the summary of the nodes operation

    :param operation: Operation type, options included ADDED/REMOVED
    :type operation: str
    :param successful_nodes: Total count of nodes added or removed successfully
    :type successful_nodes: int
    :param total_nodes: Total of the nodes to be added or removed
    :type total_nodes: int
    :param total_node_count: Total nodes in the workload pool
    :type total_node_count: int

    :return: Summary message of the operation
    :rtype: str
    """
    add_success_msg = ("\n\tNODE MANAGER SUMMARY\n\t--------------------\n\n\tNODES {0}: {1}/{2}\n\tNODE POOL SIZE: {3}"
                       "\n".format(operation, successful_nodes, total_nodes, total_node_count))
    return add_success_msg


def print_failed_remove_operation_summary(missing):
    """
    Prints a summary of the nodes that were not removed as they are not in the pool

    :param missing: List of nodes not in the workload pool
    :type missing: list

    :returns: Missing nodes message
    :rtype: str
    """
    message = ("\n\tFAILED NODES\n\t------------\nNOTE: The list of nodes below could not be removed because they are "
               "not in the pool.\n{0}".format(",".join(missing)))
    return message


def print_failed_add_operation_summary(missing_nodes):
    """
    Prints the summary of the nodes which failed to add to the pool

    :param missing_nodes: Dictionary of nodes which cannot be added to the workload pool
    :type missing_nodes: dict

    :returns: Missing nodes message
    :rtype: str
    """
    base_msg = "\nNOTE: The list of nodes below were not added because they are {0}\n"
    keys = ["NOT_ADDED", "NOT_SYNCED", "MISSING_PRIMARY_TYPE", "ALREADY_IN_POOL"]
    reasons = ["not created on ENM.", "not synced.", "not supported by the workload pool.", "already in the pool."]
    add_failure_msg = ""
    for key, reason in zip(keys, reasons):
        if missing_nodes[key]:
            add_failure_msg += "{0}\n{1}\n".format(base_msg.format(reason), ",".join(missing_nodes[key]))
    return add_failure_msg


def update_poids():
    """
    Update POID attributes on Nodes.

    POST /nodes/update_poids

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        failures_occurred = helper.update_poid_attributes_on_pool_nodes()
        message = "Failed to update POID values on {0} nodes".format(failures_occurred) if failures_occurred else ""
        success = False if failures_occurred else True
        return get_json_response(success=success, message=message)

    except Exception as e:
        abort_with_message("Failure occurred during attempt to update POID attributes", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)
