import threading

from retrying import retry
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib import log, persistence, config, mutexer
from enmutils_int.lib import node_pool_mgr, profile_properties_manager, profile_manager
from enmutils_int.lib.services.deploymentinfomanager_adaptor import poid_refresh
from enmutils_int.lib.workload_network_manager import NETWORK_TYPE, NETWORK_CELL_COUNT

DEALLOCATION_IN_PROGRESS = None
NUM_NODES = "NUM_NODES"
SUPPORTED_NODE_TYPES = "SUPPORTED_NODE_TYPES"
DEFAULT_NODES = "DEFAULT_NODES"


def update_poid_attributes_on_pool_nodes():
    """
    Update POID values on Node objects in DB

    :return: Boolean to indicate if failures occurred
    :rtype:
    """
    log.logger.debug("Updating POID attributes on Nodes in Workload Pool")
    if node_pool_mgr.cached_nodes_list:
        with mutexer.mutex("node-poid-update", log_output=True, persisted=True):
            node_poid_data = poid_refresh()

        if not node_poid_data:
            log.logger.debug("No data returned by Deployment Info Manager service - cannot update POID's on nodes")
            return len(node_pool_mgr.cached_nodes_list)

        return update_poid_attribute_on_nodes(node_poid_data)
    else:
        log.logger.debug("No nodes in pool - update not required")


def update_poid_attribute_on_nodes(node_poid_data):
    """
    Update POID attribute on Node objects

    :param node_poid_data: Dictionary of Node-POID data
    :type node_poid_data: dict
    :return: Number of failed node updates
    :rtype: int
    :raises e: if node_poid_data dictionary is empty
    """
    log.logger.debug("Updating POID attribute on {0} pool nodes (ENM nodes: {1})"
                     .format(len(node_pool_mgr.cached_nodes_list), len(node_poid_data.keys())))

    failed_nodes = 0

    with node_pool_mgr.mutex():
        for node in node_pool_mgr.cached_nodes_list:
            try:
                if len(node_poid_data) == 0:
                    raise EnmApplicationError("Length of node_poid_data is {0}".format(len(node_poid_data)))
            except EnmApplicationError as e:
                log.logger.debug("Unable to update nodes with POID info from ENM as {0}".format(e))
                raise e
            if not node_poid_data.get(node.node_id):
                log.logger.debug("Node {0} in workload pool not listed in POID data (on ENM)".format(node.node_id))
                failed_nodes += 1
                continue

            elif node_poid_data[node.node_id] != node.poid:
                node.poid = node_poid_data[node.node_id]
                try:
                    node._persist_with_mutex()
                except Exception as e:
                    log.logger.debug("Failed to update node {0} - {1}".format(node.node_id, str(e)))
                    failed_nodes += 1

    log.logger.debug("Update operation complete on {0} nodes. Failures: {1}"
                     .format(len(node_pool_mgr.cached_nodes_list), failed_nodes))
    return failed_nodes


def reset_nodes(reset_network_values=False, no_ansi=False):
    """
    Resets all nodes in the workload pool to their initial state

    :param reset_network_values: Boolean indicating if the persisted network values should be removed
    :type reset_network_values: bool
    :param no_ansi: Boolean indicating if colour logging should be disabled
    :type no_ansi: bool

    :returns: Reset message is rest performed or None if no node reset required
    :rtype: str|None
    """
    if no_ansi:
        config.set_prop("print_color", 'false')
    if reset_network_values:
        for key in [NETWORK_TYPE, NETWORK_CELL_COUNT]:
            persistence.remove(key)
        msg = log.cyan_text("\n  All persisted network values reset.\n")
    else:
        total_node_count = persistence.get('total-node-count')
        node_pool_mgr.reset()
        msg = log.cyan_text("\n  All {0} nodes reset in the pool\n".format(total_node_count))
        log.logger.debug(msg)
    return msg


def update_total_node_count(update=True):
    """
    Update the total node count if required

    :param update: Boolean indicating if the default behaviour is to update the value
    :type update: bool

    :returns: Returns the total count of nodes in the workload pool
    :rtype: int
    """
    log.logger.debug("Starting update of total-node-count key in persistence")
    total_node_key = 'total-node-count'
    if not update and persistence.has_key(total_node_key):
        total_nodes = persistence.get(total_node_key)
    else:
        pool = node_pool_mgr.get_pool()
        pool.update_node_ids()
        total_node_count = sum([len(ne_type) for ne_type in pool._nodes.itervalues()])
        total_nodes = total_node_count
        persistence.set(total_node_key, total_node_count, -1)
    log.logger.debug("Completed update of total node count.")
    return total_nodes


def determine_start_and_end_range(node_range_str):
    """
    Determine if start and end range values are supplied

    :param node_range_str: String containing start and end range or None
    :type node_range_str: str|None

    :return: Tuple containing start and end range or None and None
    :rtype: tuple
    """
    range_start = None if not node_range_str else int(node_range_str.split('-')[0])
    if not node_range_str:
        range_end = None
    elif "-" in node_range_str:
        range_end = int(node_range_str.split('-')[-1])
    else:
        range_end = range_start
    return range_start, range_end


def deallocate_profile_from_nodes(nodes, profile_name):
    """
    Deallocate the supplied profile from the supplied nodes if applicable

    :param nodes: List of `load_node.LoadNodeMixin` instances
    :type nodes: list
    :param profile_name: Name of the profile to remove from the node list
    :type profile_name: str
    """
    log.logger.debug("Deallocating profile from nodes (if allocated)")
    updated_nodes = {}
    with mutexer.mutex(node_pool_mgr.NODE_POOL_MUTEX, persisted=True, log_output=True):
        allocated_nodes = [node for node in list(set(nodes)) if node.profiles and profile_name in node.profiles]
        log.logger.debug("Profile is allocated to {0} nodes".format(len(allocated_nodes)))
        for node in allocated_nodes:
            node.profiles.remove(profile_name)
            node._is_exclusive = False
            persist_node(node)
            updated_nodes[node.node_id] = node

        if updated_nodes:
            node_pool_mgr.update_cached_list_of_nodes(updated_nodes)
    log.logger.debug("Deallocation complete")


def persist_node(node):
    """
    Function to persist a node

    :param node: Node instance to be persisted
    :type node: `load_node.LoadNodeMixin`
    """
    with mutexer.mutex("persist-{0}".format(node.node_id), persisted=True):
        persistence.default_db().set(node.node_id, node, -1, log_values=False)


def select_all_nodes_from_redis():
    """
    Select all nodes in the workload pool from redis

    :return: List of Node objects
    :rtype: list

    """
    log.logger.debug("Fetching all nodes from redis [index: {0}]".format(config.get_redis_db_index()))
    nodes = []
    node_dict = node_pool_mgr.get_pool().node_dict
    for node_type in node_dict.keys():
        nodes = nodes + node_dict[node_type].values()
    log.logger.debug("Fetched {0} node(s)".format(len(nodes)))
    return nodes


def update_cached_nodes_list():
    """
    Update list of cached nodes
    """
    log.logger.debug("Updating list of cached nodes")
    with node_pool_mgr.mutex():
        log.logger.debug("Emptying the cached list of nodes before populating")
        node_pool_mgr.cached_nodes_list = []
        node_pool_mgr.cached_nodes_list = select_all_nodes_from_redis()
    log.logger.debug("Cached list of nodes has been updated")


def set_deallocation_in_progress(profile_name=None):
    """
    Set flag to indicate that de-allocation is in progress

    :param profile_name: Name of profile
    :type profile_name: str
    :return: Message if unsuccessful otherwise None
    :rtype: str or None
    """
    global DEALLOCATION_IN_PROGRESS
    if DEALLOCATION_IN_PROGRESS:
        message = "De-allocation of nodes currently in progress by another process - retry later"
        log.logger.debug(message)
        log.logger.debug("Other thread running the de-allocation: {0}".format(DEALLOCATION_IN_PROGRESS))
        return message
    DEALLOCATION_IN_PROGRESS = "{0}_{1}".format(threading.current_thread().name, profile_name)
    log.logger.debug("De-allocation now in progress by this thread: {0}".format(DEALLOCATION_IN_PROGRESS))


def set_deallocation_complete():
    """
    Sets flag to indicate de-allocation is complete
    """
    global DEALLOCATION_IN_PROGRESS
    DEALLOCATION_IN_PROGRESS = None


def perform_deallocate_actions(profile_name, unused_nodes=None):
    """
    Performs De-allocation actions

    :param profile_name: Name of profile
    :type profile_name: str
    :param unused_nodes: String containing comma-separated list of Unused nodes
    :type unused_nodes: str
    """
    log.logger.debug("Performing de-allocation actions for {0}".format(profile_name))

    if unused_nodes:
        unused_nodes = unused_nodes.split(',')
        log.logger.debug("De-allocating {0} nodes from profile".format(len(unused_nodes)))
        nodes = [node for node in node_pool_mgr.cached_nodes_list if node.node_id in unused_nodes]
        node_pool_mgr.deallocate_unused_nodes_from_profile(nodes, profile_name)
    else:
        profile = get_profile_object_from_profile_manager(profile_name)
        log.logger.debug("De-allocating all nodes from profile")
        node_pool_mgr.deallocate_nodes(profile)

    log.logger.debug("De-allocation actions complete")


def get_profile_object_from_profile_manager(profile_name, profile_values=None):
    """
    Get profile object from Profile Manager

    :param profile_name: Name of workload profile
    :type profile_name: str
    :param profile_values: Dictionary containing key, value pairs of node allocation related variables
    :type profile_values: dict

    :return: Profile object
    :rtype: `profile.Profile`

    """

    profile_object = profile_properties_manager.ProfilePropertiesManager([profile_name]).get_profile_objects()[0]
    num_nodes = getattr(profile_object, NUM_NODES, False)
    profile_values = profile_values if profile_values else {}
    matched = any([key for key in profile_values.keys() if key in [NUM_NODES, SUPPORTED_NODE_TYPES, DEFAULT_NODES]])
    if not isinstance(num_nodes, dict) and not getattr(profile_object, SUPPORTED_NODE_TYPES, False) and not matched:
        profile_object = persistence.get(profile_name)
    profile = profile_manager.ProfileManager(profile_object).profile
    if profile_values:
        for key, value in profile_values.items():
            setattr(profile, key, value)
    return profile


def perform_allocation_tasks(profile_name, nodes, profile_values=None, network_config=None):
    """
    Perform allocation tasks

    :param profile_name: Profile Name
    :type profile_name: str
    :param nodes: Comma-separated list of node names
    :type nodes: str
    :param profile_values: Dictionary containing profile key,values to be set on the retrieved profile instance
    :type profile_values: dict
    :param network_config: Specific network configuration mapping to use
    :type network_config: str
    :raises RuntimeError: if profile name not specified
    """
    if network_config:
        config.set_prop('network_config', network_config)
    log.logger.debug("Node allocation tasks being executed by this thread")
    if not profile_name:
        raise RuntimeError("Profile name missing")
    profile = get_profile_object_from_profile_manager(profile_name, profile_values=profile_values)
    log.logger.debug("Attempting to allocate nodes to {0}".format(profile_name))
    redis_nodes = node_pool_mgr.cached_nodes_list
    if nodes:
        nodes = [node for node in redis_nodes if any([_ for _ in nodes.split(',') if _ == node.node_id])]
    deallocate_profile_from_nodes(redis_nodes, profile_name)
    node_pool_mgr.allocate_nodes(profile, nodes=nodes)
    log.logger.debug("Node allocation tasks completed")


def convert_mos_to_dictionary(node_mo_dict):
    """
    Recursive function to unpack the EnmMo instance(s)

    :param node_mo_dict: Dictionary or list depending on the MOs attributes supplied
    :type node_mo_dict: dict|list
    """
    if not getattr(node_mo_dict, "items", None):
        return
    for key, value in node_mo_dict.items():
        if any([val for val in value if getattr(val, 'mo_id', None)]):
            node_mo_dict[key] = [convert_enm_user(val.__dict__) for val in value if getattr(val, 'mo_id', None)]
        else:
            convert_mos_to_dictionary(value)


def convert_enm_user(mo_dict):
    """
    Converts the Enm User instance in the EnmMo instance to basic dictionary

    :param mo_dict: Dictionary containing the attributes of the supplied EnmMo instance
    :type mo_dict: dict

    :return: The supplied/updated dictionary
    :rtype: dict
    """
    user = mo_dict.get('user')
    if getattr(user, 'password', None):
        mo_dict['user'] = {"username": user.username, "password": user.password, "keep_password": user.keep_password,
                           "persist": user.persist, "_session_key": user._session_key}
    return mo_dict


def stringify_keys(node_mo_dict):
    """
    Convert tuple dictionary keys to string keys

    :param node_mo_dict: Dictionary or list depending on the MOs attributes supplied
    :type node_mo_dict: dict|list
    """
    if not getattr(node_mo_dict, "items", None):
        return
    for key, values in node_mo_dict.items():
        if isinstance(key, tuple):
            new_key = "|||".join(key)
            node_mo_dict[new_key] = values
            del node_mo_dict[key]
        stringify_keys(values)


def apply_cell_type_to_lte_nodes(lte_nodes, cell_dict):
    """
    Add cell type TDD/FDD to LTE node(s) if not already set

    :param lte_nodes: List of LoadNode to be checked/updated
    :type lte_nodes: list
    :param cell_dict: Dictionary containing breakdown of TDD and FDD sorted LTE nodes
    :type cell_dict: dict

    :returns: List of updated node instances
    :rtype: list
    """
    attribute = 'lte_cell_type'
    log.logger.debug("Adding LTE cell type value to nodes currently without attribute.")
    updated_nodes = []
    for cell_type, nodes in cell_dict.items():
        if cell_type in ["FDD", "TDD"]:
            for node in lte_nodes[:]:
                if not getattr(node, attribute, None) and node.node_id in nodes:
                    updated_nodes.append(persist_and_set_attr_on_node_from_node_id(node, attribute, cell_type))
                    lte_nodes.remove(node)
    log.logger.debug("Completed adding LTE cell type value to nodes currently without attribute.")
    updated_nodes.extend(
        [node for node in lte_nodes if node.node_id not in [updated_node.node_id for updated_node in updated_nodes]])
    return updated_nodes


def persist_and_set_attr_on_node_from_node_id(node, attribute, value):
    """
    Persist the node with the newly set attribute

    :param node: Instance of LoadNode to be updated and persisted
    :type node: `load_node.LoadNodeMixin`
    :param attribute: Name of the attribute to be set
    :type attribute: str
    :param value: Value of the attribute to be set
    :type value: object

    :returns: Updated instance of LoadNode
    :rtype: `load_node.LoadNodeMixin`
    """
    with mutexer.mutex("persist-{0}".format(node.node_id)):
        persisted_node = persistence.default_db().get(node.node_id)
        if persisted_node:
            log.logger.debug("Updating attribute {0} on node: {1}.".format(attribute, persisted_node.node_id))
            setattr(persisted_node, attribute, value)
            persistence.default_db().set(persisted_node.node_id, persisted_node, -1, log_values=False)
        else:
            log.logger.debug("Cannot update node attribute, node id: {0} not found in persistence.".format(
                node.node_id))
        setattr(node, attribute, value)
    return node


def retrieve_cell_information_and_apply_cell_type(allocated_nodes=None, return_updated_nodes=False, rebuild_dict=False):
    """
    Retrieve/Set the LTE cell dictionary and apply Cell types to the supplied nodes

    :param allocated_nodes: List of LoadNode to be checked/updated
    :type allocated_nodes: list|None
    :param return_updated_nodes: Boolean indicating if the list of nodes should be returned
    :type return_updated_nodes: bool
    :param rebuild_dict: Boolean indicating if we need to build the dict again due to additional nodes
    :type rebuild_dict: bool

    :returns: List of updated node instances
    :rtype: list
    """
    if not allocated_nodes:
        allocated_nodes = [node for node in node_pool_mgr.cached_nodes_list if node.primary_type in ["ERBS", "RadioNode"]]
    with node_pool_mgr.mutex():
        cell_dict = persistence.get(node_pool_mgr.EUTRANCELL_NODE_DICT)
        if not cell_dict or rebuild_dict:
            try:
                cell_dict = create_cell_dict()
            except RuntimeError as e:
                log.logger.debug("Failed to create dictionary, error encountered: [{0}]".format(str(e)))
        if cell_dict:
            allocated_nodes = apply_cell_type_to_lte_nodes(allocated_nodes, cell_dict)
    return allocated_nodes if return_updated_nodes else None


@retry(retry_on_exception=lambda e: isinstance(e, RuntimeError), wait_fixed=10000, stop_max_attempt_number=3)
def create_cell_dict():
    """
    Create and return the cell dictionary if available

    :raises RuntimeError: raised if the dict fails to create or is not retrieveable.

    :return: Dictionary containing node ids sorted by cell information
    :rtype: dict
    """
    node_pool_mgr.persist_dict_value(node_pool_mgr.EUTRANCELL)
    cell_dict = persistence.get(node_pool_mgr.EUTRANCELL_NODE_DICT)
    if cell_dict:
        return cell_dict
    raise RuntimeError("Unable to retrieve cell dict from persistence.")
