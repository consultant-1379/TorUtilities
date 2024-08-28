# ********************************************************************
# Name    : Node Pool MGR
# Summary : Responsible for all operations related to the workload
#           pool. Allows user to access the workload pool, test pool
#           and profile pool objects, allows adding, deletion,
#           updating and querying of the workload pool and profile
#           pool. Contains various functions for filtering node types,
#           supervision, host limits, cell limits, cell types and
#           numerous other filters.
# ********************************************************************
import datetime
import fnmatch
import json
import math
import random
from collections import defaultdict, OrderedDict
from contextlib import contextmanager

import jsonpickle

from enmutils.lib import persistence, log, mutexer, enm_node, enm_node_management, multitasking, process
from enmutils.lib.exceptions import (NoNodesAvailable, NotAllNodeTypesAvailable, RemoveProfileFromNodeError,
                                     AddProfileToNodeError, ScriptEngineResponseValidationError,
                                     NoOuputFromScriptEngineResponseError, TimeOutError, EnmApplicationError)
from enmutils_int.lib import network_mo_info, node_mo_selection, nss_mo_info, node_parse
from enmutils_int.lib.enm_mo import EnmMo, MoAttrs
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.load_node import NODE_CLASS_MAP

EUTRANCELL_NODE_DICT = "eutrancell-node-dict"
EUTRANCELL = "EUTRANCELL"
LARGE_BSC = "large-bsc-nodes"
SMALL_BSC = "small-bsc-nodes"
BSC_250_CELL = "bsc-250-cell-nodes"
KEY_MAPPINGS = {EUTRANCELL: EUTRANCELL_NODE_DICT, "LARGE_BSC": LARGE_BSC, "SMALL_BSC": SMALL_BSC,
                "BSC_250_CELL": BSC_250_CELL}
NOTALLNODESCMSYNCKEY = "nodes available ("
ACTIVE_WORKLOAD_PROFILES = "active_workload_profiles"
PROFILE_NOTIFICATION_VALUES = "cmsync-profile-notifications"
PROFILE_NODE_ALLOCATION_VALUES = "cmsync-node-allocations"
UPDATED_NODES = {"SGSN-MME": "SGSN", "MINI-LINK-Indoor": "MLTN", "CISCO-ASR900": "CISCO",
                 "FRONTHAUL-6080": "FrontHaul-6080", "Router6672": "Router_6672", "Router6274": "Router_6274"}

cached_nodes_list = []
LTE_DICT = {}
NODE_POOL_MUTEX = "node-mgr-pool-operation"
DB_KEY = '%s-mos'


def initialize_cached_nodes_list():
    """
    Initializes a global variable to cache the list of persisted nodes from the DB
    """
    global cached_nodes_list
    cached_nodes_list = []


def persist_after(func):
    # A decorator function which will persist pool after running the calling function
    # For decorator pattern please read
    # http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/

    def wrapper(pool, *args, **kwargs):
        # Invoke decorated function
        return_value = func(pool, *args, **kwargs)

        # Persist updated node pool
        pool.persist()

        # Return output from decorated function
        return return_value

    return wrapper


def has_node(node_id):
    """
    Checks to see if the node is already in the database

    :param node_id: Key to search for on the Database
    :type node_id: str
    :return: True if key was found in the database, False otherwise
    :rtype: bool

    """
    return persistence.has_key(node_id)


def get_node(node_id):
    """
    Retrieves node from persistence using the node id as the key used to locate the node

    :param node_id: Key to search for in persistence
    :type node_id: str
    :return: A value from persistence
    :rtype: primitive or object; None if the key doesn't exist

    """
    return persistence.get(node_id)


# It should be considered to move this function to persistence.
def remove_node(node_id):
    """
    Removes a node from persistence
    :param node_id: Key to search for on the Database
    :type node_id: str


    """
    persistence.remove(node_id)


@contextmanager
def mutex(timeout=None):
    """
    This mutex ensures only one process can update the ProfilePool at any point in time.
    Note: The 'node-mgr-pool-operation' mutex does not expire as the allocation procedure should be allowed to complete
    before the mutex is released by the process performing the allocation, to avoid inconsistencies in allocated nodes.
    :type timeout: int
    """
    with mutexer.mutex(NODE_POOL_MUTEX, persisted=True, timeout=timeout, log_output=True):
        yield


def add(*args, **kwargs):
    """
    Interface to use for adding nodes to ProfilePool.
    The mutex ensures only one process can update the ProfilePool at any point in time
    """
    with mutex():
        return get_pool().add(*args, **kwargs)


def remove(path, start=None, end=None, force=None):
    """
    Interface to use for removing nodes from ProfilePool.
    The mutex ensures only one process can update the ProfilePool at any point in time
    """
    with mutex():
        return get_pool().remove(path, start=start, end=end, force=force)


def remove_all(force=None):
    """
    Interface to use for remove all nodes from the ProfilePool.
    The mutex ensures only one process can update the ProfilePool at any point in time
    """
    with mutex():
        return get_pool().remove_all(force=force)


def exchange_nodes(profile):
    """
    Interface used for interacting with the workload pool to exchange the node(s) that have a profile assigned to them.

    :param profile: the profile that will be removed from its existing node(s) and allocated to new node(s)
    :type profile: enmutils_int.lib.profile.Profile object
    """
    process.get_current_rss_memory_for_current_process()
    log.logger.debug(
        'Entering Exchange Nodes Pool Interface - Attempting to exchange the nodes tied to profile: "{}"'.format(
            profile))
    initialize_cached_nodes_list()
    multitasking.create_single_process_and_execute_task(exchange_nodes_allocated_to_profile, args=(profile.NAME, ))
    log.logger.debug('Exiting Exchange Nodes Pool Interface - Successfully executed the exchange nodes flow.')
    process.get_current_rss_memory_for_current_process()


def allocate_nodes(profile, nodes=None):
    """
    Interface used for interacting with the mutexed workload pool to allocate a profile to node(s).

    :param profile: the profile which will be allocated to the node(s)
    :type profile: enmutils_int.lib.profile.Profile object
    :param nodes: a list of nodes to allocate a profile to
    :type nodes: list
    """

    log.logger.debug(
        'Allocate Nodes Pool Interface - Attempting to allocate the profile: "{}" to nodes'.format(
            profile))
    with mutex():
        get_pool().allocate_nodes(profile=profile, nodes=nodes)

    log.logger.debug('Successfully allocated the profile: "{}" to nodes'.format(profile))


def deallocate_nodes(profile):
    """
    Interface to use for de-allocating nodes to profiles in ProfilePool.
    The mutex ensures only one process can update the ProfilePool at any point in time
    """
    with mutex():
        get_pool().deallocate_nodes(profile)


def deallocate_unused_nodes(nodes, profile_name):
    """
    Deallocate the unused nodes via separate process

    :type nodes: list
    :param nodes: List of `enm_node.Node` objects
    :type profile_name: str
    :param profile_name: Name of the profile to remove from the node(s)
    """
    process.get_current_rss_memory_for_current_process()
    log.logger.debug("De-allocating unused nodes")
    multitasking.create_single_process_and_execute_task(deallocate_unused_nodes_from_profile,
                                                        args=(nodes, profile_name), fetch_result=False)
    log.logger.debug("De-allocating unused nodes complete")
    process.get_current_rss_memory_for_current_process()


def deallocate_unused_nodes_from_profile(nodes, profile_name):
    """
    Deallocate the unused nodes

    :type nodes: list
    :param nodes: List of `enm_node.Node` objects
    :type profile_name: str
    :param profile_name: Name of the profile to remove from the node(s)
    """
    with mutex():
        remove_profile_from_nodes(nodes, profile_name)


def remove_profile_from_nodes(nodes, profile_name):
    """
    Deallocate the unused nodes

    :type nodes: list
    :param nodes: List of `enm_node.Node` objects
    :type profile_name: str
    :param profile_name: Name of the profile to remove from the node(s)
    """
    global cached_nodes_list
    log.logger.debug("Number of nodes to be de-allocated: {0}".format(len(nodes)))
    deallocated_nodes_count = 0
    updated_nodes = dict()
    for node in nodes:
        with mutexer.mutex("persist-{}".format(node.node_id), persisted=True, log_output=False):
            if profile_name in node.profiles[:]:
                persisted_node = persistence.get(node.node_id)
                persisted_node.profiles.remove(profile_name)
                persisted_node._is_exclusive = False
                persisted_node._persist()
                deallocated_nodes_count += 1
                updated_nodes[node.node_id] = persisted_node
            else:
                log.logger.debug("Node {0} not allocated to profile {1}".format(node.node_id, profile_name))

    if cached_nodes_list:
        update_cached_list_of_nodes(updated_nodes)

    log.logger.debug("Number of nodes de-allocated: {0}".format(deallocated_nodes_count))


def reset():
    """
    Interface to use for resetting errors on nodes in ProfilePool.
    The mutex ensures only one process can update the ProfilePool at any point in time
    """
    with mutex():
        get_pool().reset()


def get_pool():
    """
    Retrieves nodes from persistence using the workload_pool identifier key. If no nodes, returns empty pool.
    rtype: primitive or object; None if the key doesn't exist

    """

    return persistence.get("workload_pool") or ProfilePool()


def group_nodes_per_sim(nodes_list):
    """
    Builds a dictionary where it groups netsim hosts and their simulations
    and then stores it in cache. It stores the node names and not the node objects

    :param nodes_list: List of the profile node objects to group per netsim host and simulation
    :type nodes_list: List
    :return: multidimensional dictionary containing host, sim and node data
    :rtype: dict

    """

    network_dict = {}
    for node in nodes_list:
        if node.netsim not in network_dict:
            network_dict[node.netsim] = {}
        if node.simulation not in network_dict[node.netsim]:
            network_dict[node.netsim][node.simulation] = []
        network_dict[node.netsim][node.simulation].append(node)

    return network_dict


def get_random_available_nodes(profile, node_type):
    """
    Interface to use to get nodes available to the profile, given the node type

    :param profile: profile to get nodes for
    :type profile: enmutils_int.lib.profile.Profile
    :param node_type: type of node required
    :type node_type: str
    :return: random available nodes for the profile
    :rtype: list
    """

    return get_pool().get_random_available_nodes(profile=profile, node_type=node_type)


class Pool(object):

    def __init__(self):
        self._nodes = {key: [] for key in NODE_CLASS_MAP.keys()}
        self.key = self.PERSISTENCE_KEY
        self.update_node_ids()

    def update_node_ids(self):
        """
        Update the existing workload pool node ids to mirror persistence
        """
        missing_node_persisted_nodes = get_all_nodes_from_redis(
            [node for ne_type in self._nodes.values() for node in ne_type])
        for node in missing_node_persisted_nodes:
            if node.node_id not in self._nodes.get(node.primary_type):
                self._nodes[node.primary_type].append(node.node_id)

    @property
    def nodes(self):
        """
        List containing the  pool nodes

        :return: List containing `load_node.LoadNode` instances
        :rtype: list
        """
        log.logger.debug("Reading nodes property")
        global cached_nodes_list
        if cached_nodes_list:
            log.logger.debug("Using cached nodes list")
            nodes = cached_nodes_list
        else:
            nodes = []
            log.logger.debug("Reading nodes from DB")
            for node_type in self._nodes.keys():
                nodes = nodes + self.db.get_keys([node for node in self._nodes[node_type] if self.db.has_key(node)])
            cached_nodes_list = nodes
        log.logger.debug("Reading nodes property complete")
        return nodes

    @property
    def wl_nodes(self):
        """
        List containing the pool nodes and it's always getting nodes from persistence

        :return: List containing `load_node.LoadNode` instances
        :rtype: list
        """
        log.logger.debug("Reading nodes property")
        nodes = []
        log.logger.debug("Reading nodes from DB")
        for node_type in self._nodes.keys():
            nodes = nodes + self.db.get_keys([node for node in self._nodes[node_type] if self.db.has_key(node)])
        log.logger.debug("Reading nodes property complete")
        return nodes

    @property
    def node_dict(self):
        """
        Return dictionary of nodes per node type

        :return: dictionary of nodes
        :rtype: dict
        """
        log.logger.debug("Reading node dict property")
        process.get_current_rss_memory_for_current_process()
        node_dict = {}
        for node_type in self._nodes.keys():
            node_dict[node_type] = {}

        for key in node_dict.keys():
            for node_name in NODE_CLASS_MAP.keys():
                if node_name != key:
                    node_dict[node_name] = {}

        nodes = self.nodes
        log.logger.debug("Populating node dict using list of nodes")
        for node in nodes:
            for node_type in self._nodes.keys():
                if node.node_id in self._nodes[node_type]:
                    node_dict[node_type][node.node_id] = node

        log.logger.debug("Reading node dict property complete")
        process.get_current_rss_memory_for_current_process()
        return node_dict

    def filter(self, node_names):
        """
        Filters active nodes given the list of node names

        :param node_names: list of strings
        :type node_names: list
        :return: dictionary of filtered nodes
        :rtype: dict

        """
        log.logger.debug("Filtering active nodes based on node names")
        nodes = {}
        node_dict = self.node_dict
        for node_type in node_dict.keys():
            pool_node_names = node_dict[node_type].keys()
            for name in node_names:
                if name in pool_node_names:
                    nodes[name] = node_dict[node_type][name]
        log.logger.debug("Filtering active nodes based on node names complete")
        return nodes

    def grep(self, patterns):
        """
        Filters active nodes given the string pattern to match against node names

        :param patterns: list of string patterns (unix style) against which node names will be compared;
                        if the pattern is in the node name, it will be returned
        :type patterns: list
        :rtype: dict
        :return: dictionary of nodes

        """

        nodes = {}
        node_dict = self.node_dict
        for node_type in node_dict.keys():
            for name in node_dict[node_type]:
                # fnmatch uses unix style file pattern match instead of regular expressions. So
                # the behaviour of grep is consistent with the unix style find/grepping.
                if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                    nodes[name] = node_dict[node_type][name]

        return nodes

    @staticmethod
    def _load_nodes_from_file(file_path, remove_operation=False, node_map=None, start_range=None, end_range=None):
        """
        Reads node data from the specified file and creates load_node.Node subclass instances for the nodes

        :param file_path: absolute path of the node data file to be read
        :type file_path: str
        :param remove_operation: Boolean indicating the operation is to remove or add nodes
        :type remove_operation: bool
        :param node_map: keys are the different types of node names and values are the instances of that node
        :type node_map: dict
        :param start_range: Start range of the supplied input file
        :type start_range: int
        :param end_range: End range of the supplied input file
        :type end_range: int

        :return: list of nodes or tuple(uncreated nodes if the operation is add)
        :rtype: list | tuple
        """
        node_map = node_map or NODE_CLASS_MAP
        valid_nodes = []
        if not remove_operation:
            node_dicts, nodes_not_created = node_parse.get_node_data(file_path, start_range=start_range,
                                                                     end_range=end_range)
        else:
            node_names = node_parse.get_node_names_from_xml(file_path, start_range=start_range, end_range=end_range)
            not_in_pool = [node_name for node_name in node_names if not persistence.has_key(node_name)]
            node_dicts = [persistence.get(node_name).__dict__ for node_name in set(node_names).difference(not_in_pool)]
            return [node_map["BaseLoadNode"](**node_dict) for node_dict in node_dicts], not_in_pool
        for node_dict in node_dicts:
            primary_type = node_dict["primary_type"]
            if primary_type in node_map:
                valid_nodes.append(node_map[primary_type](**node_dict))
            else:
                valid_nodes.append(node_map["BaseLoadNode"](**node_dict))
        return valid_nodes, nodes_not_created

    def add(self, path, start=None, end=None, node_map=None, profiles=None, validate=False):
        """
        Add nodes given the path to csv and start and end ranges

        :param path: path to csv file
        :type path: str
        :param start: start range
        :type start: int
        :param end: end range
        :type end: int
        :param node_map: dictionary of node name and node
        :type node_map: dict
        :param profiles: list of profiles that these nodes should be available to
        :type profiles: list
        :param validate: whether to validate
        :type validate: bool

        :return: Tuple where first element is list of nodes added, second element is dictionary of nodes not added
        :rtype: tuple

        """
        self._update_node_dict()
        node_map = node_map or NODE_CLASS_MAP
        nodes_to_check, not_created = self._load_nodes_from_file(path, node_map=node_map, start_range=start,
                                                                 end_range=end)
        missing_nodes = {"ALREADY_IN_POOL": [], "NOT_ADDED": not_created, "NOT_SYNCED": [], "MISSING_PRIMARY_TYPE": []}
        added, not_synced = [], []

        if validate:
            not_synced = self.validate_nodes_against_enm()
        for node in nodes_to_check:
            if node.primary_type not in self._nodes.keys() or not self._nodes[node.primary_type]:
                self._nodes[node.primary_type] = []
            log.logger.debug("")
            if not node.primary_type:
                log.logger.info("The primary type {0} does not exist for node {1}".format(node.primary_type,
                                                                                          node.node_id))
                missing_nodes["MISSING_PRIMARY_TYPE"].append(node.node_id)
                continue
            if profiles:
                node.available_to_profiles |= set(profiles)
            if node.node_id in self._nodes[node.primary_type]:
                missing_nodes["ALREADY_IN_POOL"].append(node.node_id)
            elif validate and node.node_id in not_synced:
                missing_nodes["NOT_SYNCED"].append(node.node_id)
            else:
                self._nodes[node.primary_type].append(node.node_id)
                node = update_lte_node(node)
                node._persist()
                self.persist()
                log.logger.debug("Successfully ADDED node: '{0}' to the workload pool and persistence."
                                 .format(node.node_id))
                added.append(node.node_id)
        return added, missing_nodes

    @staticmethod
    def validate_nodes_against_enm():
        """
        Retrieve the sync status of ENM created nodes

        :return: List of nodes currently not synchronized
        :rtype: list
        """
        user = get_workload_admin_user()
        supervised_nodes = enm_node_management.CmManagement.get_status(user)
        not_synced = [node.node_id for node in supervised_nodes if supervised_nodes[node] != "SYNCHRONIZED"]
        return not_synced

    @persist_after
    def remove(self, path, start=None, end=None, force=False):
        """
        Remove nodes from the pool given the path to csv file

        :param path: path to csv file
        :type path: str
        :param start: number of the first node in the csv that you want to start removing from
        :type start: int
        :param end: number of the last node in the csv that you want removed
        :type end: int
        :param force: True will remove the node from the pool regardless of whether there are profiles using that node,
                    False won't
        :type force: bool
        :return: first element is a list of node names removed from the pool, second is a list of node names missing
                from the pool, third is a list of node names with profile(s) allocated to them
        :rtype: tuple
        """

        nodes_to_check, missing = self._load_nodes_from_file(path, remove_operation=True, start_range=start,
                                                             end_range=end)
        # One is based on values found in persistence, the second the pool's own list of nodes
        pool_nodes = self.node_dict
        pool_nodes_dict = self._nodes
        removed, allocated = [], []
        for node in missing:
            for key, values in pool_nodes_dict.iteritems():
                if node in values:
                    pool_nodes_dict[key].remove(node)
        for node in nodes_to_check:
            if node.node_id in pool_nodes[node.primary_type].keys():
                if not force and pool_nodes[node.primary_type][node.node_id].profiles:
                    allocated.append(node.node_id)
                    continue
                pool_nodes_dict[node.primary_type].remove(node.node_id)
                remove_node(node.node_id)
                log.logger.debug("Successfully REMOVED node: '{0}' from the workload pool and persistence."
                                 .format(node.node_id))
                removed.append(node.node_id)
        return removed, missing, allocated

    def remove_all(self, force=None):
        """
        Only remove all nodes if not in use

        :type force: bool
        :param force: Optional boolean to override checks and remove all

        :return: True or False
        :rtype: bool

        """

        all_nodes_removed = False
        if not self._is_in_use() or force:
            self.db.remove('workload_pool')
            for node_type in self._nodes.keys():
                for node_name in self._nodes[node_type]:
                    remove_node(node_name)
            all_nodes_removed = True

        return all_nodes_removed

    def reset(self):
        """
        Only resets all nodes if not in use or no active profiles
        """
        log.logger.debug("Attempting to reset all available nodes.")
        active_profiles = persistence.get("active_workload_profiles")
        all_nodes = self.nodes
        if not self._is_in_use() or not active_profiles:
            for node in all_nodes:
                node.reset()
        else:
            # Filter out exclusive nodes but handle the situation where a profile has manually allocated
            exclusive_nodes = [node for node in all_nodes if node.is_exclusive and len(node.profiles) <= 1]
            for node in exclusive_nodes:
                if not node.profiles or node.profiles[0] not in active_profiles:
                    node.reset()

    def jsonify(self, nodes=None):
        """
        Serialize the given nodes into a json format in a tree hierarchy

        :param nodes: list of nodes
        :type nodes: list
        :return: nodes in json format
        :rtype: str
        """
        netsims_list = []
        netsims_dict = {"netsims": netsims_list}
        grouped_nodes = group_nodes_per_sim(nodes or self.nodes)
        for host, sims in sorted(grouped_nodes.iteritems(), key=lambda item: item[0]):
            sims_list = []
            host_dict = {"name": host, "simulations": sims_list}
            for sim, list_of_nodes in sorted(sims.iteritems(), key=lambda item: item[0]):
                nodes_list = []
                sim_dict = {"name": sim, "nodes": nodes_list}
                for node in sorted(list_of_nodes):
                    nodes_list.append(jsonpickle.encode(node.__dict__))
                sims_list.append(sim_dict)
            netsims_list.append(host_dict)

        return json.dumps(netsims_dict)

    def _is_in_use(self):
        """
        Checks to see if a profile is running on any node in the pool
        :return: True is node is in use by a profile, otherwise False
        :rtype: bool
        """
        return any(node.used for node in self.nodes)

    def _node_is_used_by(self, node, profile):
        """
        Identifies whether the node passed in is being used by the profile passed in.

        :param node: node to check
        :type node: enmutils.lib.load_node.LoadNodeMixin
        :param profile: profile to check
        :type profile: enmutils_int.lib.profile.Profile

        :return: True if the node is being used by the profile else False
        :rtype: bool
        """
        return str(profile) in node.profiles

    def get_available_nodes(self, profile):
        """
        Gets a list of available nodes the specified profile could be assigned to

        :param profile: the profile to be checked if the nodes can be assigned to it
        :type profile: enmutils_int.lib.profile.Profile
        :return: list of nodes
        :rtype: list

        :raises NoNodesAvailable: raised if there are no nodes available for the profile
        """
        profile_name = getattr(profile, "NAME", "Non-profile")
        log.logger.debug("Determine nodes available for use by profile: {0}".format(profile_name))
        node_dict = self.node_dict

        if hasattr(profile, 'NUM_NODES') and profile.NUM_NODES == {}:
            log.logger.debug("Profile requires all nodes")
            return self.get_random_available_nodes(profile, node_dict=node_dict)

        nodes_filled = False
        available_nodes = []

        if getattr(profile, 'SUPPORTED_NODE_TYPES', None) and getattr(profile, 'TOTAL_NODES', 0):
            available_nodes = self.allocate_nodes_by_ne_type(profile, node_dict=node_dict)
        else:
            for node_type, num_nodes in sorted(getattr(
                    profile, 'NUM_NODES', {}).items(), reverse=True, key=lambda item: item[1]):
                log.logger.debug("Number of {0} nodes required by profile: {1}".format(node_type, num_nodes))
                available_nodes_of_type = self.get_random_available_nodes(
                    profile=profile, num_nodes=num_nodes if num_nodes != -1 else None, node_type=node_type,
                    node_dict=node_dict)
                available, nodes_filled = self.select_available(num_nodes, nodes_filled, profile, available_nodes,
                                                                available_nodes_of_type)
                available_nodes += available
        if profile_name == "HA_01":
            available_nodes = self.adjust_node_allocation_based_on_available_node_types(available_nodes)
        if not available_nodes:
            node_types = (', '.join(profile.NUM_NODES) if getattr(profile, 'NUM_NODES', None) else
                          ', '.join(getattr(profile, 'SUPPORTED_NODE_TYPES', "")))
            node_types = self.add_filtered_node_types_in_message(node_types, profile)

            raise NoNodesAvailable('No available {0} nodes for item {1}.'.format(node_types, str(profile)))

        log.logger.debug("Number of available nodes (for types specified by profile): {0}".format(len(available_nodes)))
        return available_nodes

    @staticmethod
    def adjust_node_allocation_based_on_available_node_types(nodes_available):
        """
        Check if ERBS and RadioNoides are available for the profile.
        If so, allocate only ERBS nodes and remove RadioNodes
        :param nodes_available: Nodes available in the pool for the profile
        :type nodes_available: list
        :return: list of nodes usable for the profile
        :rtype: list
        """
        node_type_dict = {}
        required_nodes = []
        for node in nodes_available:
            key = node.primary_type
            if key not in node_type_dict.keys():
                node_type_dict[key] = []
            node_type_dict[key].append(node)
        if 'ERBS' in node_type_dict.keys() and 'RadioNode' in node_type_dict.keys():
            node_type_dict.pop('RadioNode')
            for nodes_list in node_type_dict.values():
                required_nodes.extend(nodes_list)
        return required_nodes if required_nodes else nodes_available

    @staticmethod
    def add_filtered_node_types_in_message(node_types, profile):
        """
        Adds the node filter information when nodes not found on deployment

        :param node_types: Specific node type or "all"
        :type node_types: str
        :param profile: profile to get nodes for
        :type profile: `lib.profile.Profile`

        :return: Returns the same node_types if profile does not have NODE_FILTER or adds the filter information to message
        :rtype: str
        """
        if (hasattr(profile, 'NODE_FILTER') and 'RadioNode' in profile.NODE_FILTER.keys() and
                'managed_element_type' in profile.NODE_FILTER['RadioNode'].keys()) and 'RadioNode' in node_types:
            node_types = node_types.replace('RadioNode', 'RadioNode (Node Filter: {0})'.format(
                str(profile.NODE_FILTER.get('RadioNode').get("managed_element_type"))))

        return node_types

    @staticmethod
    def select_available(num_nodes, nodes_filled, profile, available_nodes, available_nodes_of_type):
        """
        Select the available nodes based upon the supplied inputs

        :param num_nodes: Number of nodes required
        :type num_nodes: int
        :param nodes_filled: Boolean flag indicating if the nodes requirement is met
        :type nodes_filled: bool
        :param profile: Profile instance requiring nodes
        :type profile: `Profile`
        :param available_nodes: List of the currently available nodes
        :type available_nodes: list
        :param available_nodes_of_type: List of the currently available nodes of a specific NE type
        :type available_nodes_of_type: list

        :raises ValueError: raised if num_nodes is set to -1 twice and total_nodes is specified

        :return: Tuple containing the list of available nodes, update boolean value of nodes_filled
        :rtype: tuple
        """
        if num_nodes == -1 and hasattr(profile, 'TOTAL_NODES'):
            if nodes_filled:
                raise ValueError('Can not specify TOTAL_NODES value and query for all nodes on multiple node types')
            num_nodes_to_get = profile.TOTAL_NODES - len(available_nodes)
            num_to_get = num_nodes_to_get if num_nodes_to_get < len(available_nodes_of_type) else len(
                available_nodes_of_type)
            return distribute_nodes(available_nodes_of_type, num_to_get), True
        else:
            return available_nodes_of_type, False

    def handle_backward_compatibility(self, node_list, node_type=None, node_dict=None):
        """
        Handle backward compatibility for certain node names in node pool (e.g. Router_6672 vs Router6672)

        :param node_list: list of nodes
        :type node_list: list
        :param node_type: Node type
        :type node_type: str
        :param node_dict: Dictionary containing the currently available nodes
        :type node_dict: dict
        :return: List of Node objects
        :rtype: list
        """
        log.logger.debug("Checking for backward-compatible nodes in pool for node_type: {0}".format(node_type))
        node_dict = node_dict if node_dict else self.node_dict
        if node_type and node_type in UPDATED_NODES.keys():
            log.logger.debug("Number of {0} nodes: {1}".format(node_type, len(node_dict[node_type].values())))
            backward_compatible_node_type = UPDATED_NODES.get(node_type)
            if (backward_compatible_node_type in node_dict.keys() and
                    len(node_dict[backward_compatible_node_type].values())):
                log.logger.debug("Filtering nodes to include backward-compatible {0} nodes"
                                 .format(backward_compatible_node_type))

                node_list += node_dict[backward_compatible_node_type].values()
                log.logger.debug("{0} extra {1} node(s) added"
                                 .format(len(node_dict[backward_compatible_node_type].values()),
                                         backward_compatible_node_type))

        return node_list

    def get_random_available_nodes(self, profile, num_nodes=None, node_type=None, exclude_nodes=None, node_dict=None):
        """
        Get random available nodes for the profile

        :param profile: profile to get nodes for
        :type profile: enmutils_int.lib.profile.Profile
        :param num_nodes: number of nodes required
        :type num_nodes: int
        :param node_type: type of nodes required
        :type node_type: str
        :param exclude_nodes: list of node_ids to be excluded
        :type exclude_nodes: list
        :param node_dict: Dictionary containing the currently available nodes
        :type node_dict: dict

        :return: list of nodes
        :rtype: list
        """
        node_type_str = node_type or 'all'
        log.logger.debug("Getting random nodes for type: {0}".format(node_type_str))
        node_dict = node_dict if node_dict else self.node_dict

        all_nodes = node_dict[node_type].values() if node_type else self.nodes
        log.logger.debug("Number of {0} nodes: {1}".format(node_type_str, len(all_nodes)))

        all_nodes = self.handle_backward_compatibility(all_nodes, node_type, node_dict)
        log.logger.debug("Number of nodes after backward compatibility checks: {0}".format(len(all_nodes)))

        all_nodes = match_cardinality_requirements(profile, all_nodes, node_type)
        log.logger.debug("Number of nodes after checking cardinality reqs: {0}".format(len(all_nodes)))

        all_nodes = self.remove_upgind_nodes(profile, all_nodes)
        log.logger.debug("Number of nodes after removing release independence nodes: {0}".format(len(all_nodes)))

        if not hasattr(profile, 'NAME') or not profile.NAME == "SHM_27":
            available_nodes = NodesFilter(profile, all_nodes, node_type, exclude_nodes=exclude_nodes).execute()
            log.logger.debug("Number of nodes after applying NodesFilter: {0}".format(len(available_nodes)))
        else:
            available_nodes = all_nodes

        node_type_str = self.add_filtered_node_types_in_message(node_type_str, profile)
        error_message = self.determine_if_nodes_not_available(available_nodes, node_type_str, profile, node_type)
        if num_nodes:
            if len(available_nodes) < num_nodes:
                error_message = ('Required num of nodes {0} of type {1} for {2} is greater than {4}{3})'
                                 .format(num_nodes, node_type_str, str(profile), len(available_nodes),
                                         NOTALLNODESCMSYNCKEY))
            else:
                available_nodes = distribute_nodes(available_nodes, num_nodes)
                log.logger.debug("Number of nodes after distribution across netsims: {0}".format(len(available_nodes)))

        if error_message:
            log.logger.debug(error_message)
            self.determine_if_environ_warning_to_be_added_to_profile(error_message, profile)
        if getattr(profile, "CHECK_NODE_SYNC", False):
            available_nodes = filter_unsynchronised_nodes(available_nodes, ne_type=node_type)
            log.logger.debug("Number of nodes after filtering unsynchronized nodes: {0}".format(len(available_nodes)))

        if "RadioNode" in node_type_str and profile.NAME in ["CMIMPORT_31", "CMIMPORT_32", "CMIMPORT_33"]:
            available_nodes = [node for node in available_nodes if node.lte_cell_type == "FDD"]
            log.logger.debug("Number of FDD nodes after filtering available nodes: {0} node(s)".format(len(available_nodes)))
        log.logger.debug("Number of available random {0} node(s) fetched: {1}"
                         .format(node_type_str, len(available_nodes)))
        return available_nodes

    @staticmethod
    def determine_if_nodes_not_available(available_nodes, node_type_str, profile, node_type):
        """
        Check if the required node is available

        :param available_nodes: List of currently available nodes
        :type available_nodes: list
        :param node_type_str: Specific node type or "all"
        :type node_type_str: str
        :param profile: profile to get nodes for
        :type profile: `lib.profile.Profile`
        :param node_type: NE Type required to be allocated
        :type node_type: str

        :raises NoNodesAvailable: raised if no nodes found in the pool when node type is None

        :return: Error message if any
        :rtype: str
        """
        error_message = ''
        if not available_nodes:
            error_message = 'No nodes of type {0} found for {1}'.format(node_type_str, str(profile))
            if node_type is None:
                raise NoNodesAvailable('No nodes found in the pool for {0}'.format(str(profile)))
        return error_message

    @staticmethod
    def determine_if_environ_warning_to_be_added_to_profile(error_message, profile):
        """
        Determines if EnvironWarning needs to be added to certain profiles which adjust rates
        :param error_message: Content of the error message to be added to the profile
        :type error_message: str
        :param profile: Profile object to add an error to
        :type profile: `Profile`
        """
        log.logger.debug("Determine if environ warnings needs to be added to the profile")
        profile_name = getattr(profile, "NAME", "Non-profile")
        fm_alarm_profiles = ["FM_0{}".format(_) for _ in range(1, 4)]
        actual_allocated = error_message.split(NOTALLNODESCMSYNCKEY)[-1].split(')')[0]
        if profile_name not in (["CMSYNC_SETUP"] + ["CMSYNC_0{0}".format(_) for _ in range(2, 7, 2)] +
                                fm_alarm_profiles):
            allowable_min_node_count = getattr(profile, 'MINIMUM_ALLOWABLE_NODE_COUNT', 0)
            if (allowable_min_node_count and actual_allocated.isdigit() and
                    int(actual_allocated) >= allowable_min_node_count):
                return
            profile.add_error_as_exception(NotAllNodeTypesAvailable(error_message))
        if actual_allocated.isdigit() and int(actual_allocated) >= 1 or (profile_name in fm_alarm_profiles):
            return
        else:
            profile.add_error_as_exception(NotAllNodeTypesAvailable(error_message))

    @staticmethod
    def remove_upgind_nodes(profile, available_nodes):
        """
        Filter out any nodes with UPGIND in the sim name

        :param profile: Profile object requesting the nodes
        :type profile: `Profile`
        :param available_nodes: List of ENM node objects
        :type available_nodes: list

        :return: List of ENM node objects
        :rtype: list
        """
        if getattr(profile, "NO_UPGIND", False):
            available_nodes = [node for node in available_nodes if "UPGIND" not in node.simulation]
        return available_nodes

    def allocated_nodes(self, item):
        """
        Given the item, returns all the nodes allocated to it

        :param item: profile which is assigned to the node
        :type item: enmutils_int.lib.profile.Profile or str
        :return: list of node objects
        :rtype: list
        """
        log.logger.debug("Getting list of currently allocated nodes ")
        return list(set([node for node in self.nodes if self._node_is_used_by(node, item)]))

    def allocated_nodes_as_dict(self, item):
        """
        Given the item, returns all the nodes allocated to it
        :param item: object which is assigned to the node
        :type item: enmutils_int.lib.profile.Profile
        :return: dict of Node types with nodes as values
        :rtype: dict
        """

        used_nodes = defaultdict(list)

        for node in self.nodes:
            if self._node_is_used_by(node, item):
                used_nodes[node.primary_type].append(node)

        return used_nodes

    def persist(self):
        """
        Persists the pool in the redis db
        :raises RuntimeError
        """
        self.db.set(self.key, self, -1)

    def clear(self):
        """
        Removes the node pool from persistence
        """
        self.db.remove(self.key)

    @staticmethod
    def update_node_types(profile, node_dict):
        """
        Update supported node types list, editing Non-backwards compatible nodes

        :param profile: Profile object to allocate nodes to
        :type profile: `profile.Profile`
        :param node_dict: Dictionary containing the Key/Value pairings of NodeTypes/Nodes
        :type node_dict: dict
        :return: List of node types
        :rtype: list
        """
        node_types = []
        for node_type in profile.SUPPORTED_NODE_TYPES:
            if node_type in UPDATED_NODES.keys():
                updated_node_type = UPDATED_NODES[node_type]
                if node_type in node_dict.keys() and not node_dict[node_type]:
                    node_types.append(updated_node_type)
                elif updated_node_type in node_dict.keys() and node_dict[updated_node_type]:
                    node_types.append(node_type)
                    node_types.append(updated_node_type)
                else:
                    node_types.append(node_type)
            else:
                node_types.append(node_type)
        return list(set(node_types))

    def allocate_nodes_by_ne_type(self, profile, node_dict=None):
        """
        Allocates nodes for profile(s) using SUPPORTED NODE TYPES

        :param profile: Profile instance requesting nodes
        :type profile: `lib.profile.Profile`
        :param node_dict: Dictionary containing the nodes in the pool
        :type node_dict: dict
        :return: List of available nodes selected.
        :rtype: list
        """
        log.logger.debug("Starting allocate nodes by ne type.")
        ne_types = getattr(profile, 'SUPPORTED_NODE_TYPES', [])
        determined_requirements = self.set_expected_total_nodes_by_type(profile, ne_types, node_dict)
        all_available_nodes = self.get_all_available_nodes_for_supported_node_types_attribute(profile, ne_types, node_dict)
        updated_requirements = self.correct_ne_type_under_allocation(self.determine_if_ne_type_under_allocation(
            determined_requirements, all_available_nodes), determined_requirements)
        if getattr(profile, 'NAME', "") == "FM_01":
            updated_requirements = self.update_bsc_node_requirements_for_fm(all_available_nodes, updated_requirements,
                                                                            profile)
            log.logger.debug("Updated requirements : {0}".format(updated_requirements))
        available_nodes = self.select_ne_type_available_nodes(updated_requirements, all_available_nodes)
        log.logger.debug("Completed allocate nodes by ne type.")
        return available_nodes[:getattr(profile, 'TOTAL_NODES', -1)]

    @staticmethod
    def update_bsc_node_requirements_for_fm(all_available_nodes, updated_requirements, profile):
        """
        :param all_available_nodes: all the available nodes for allocation to the profile
        :type all_available_nodes: dict
        :param updated_requirements: dictionary containing the node types and their required count
        :type updated_requirements: dict
        :param profile: Profile instance requesting nodes
        :type profile: `lib.profile.Profile`
        :return: dictionary with updated BSC node count
        :rtype: dict
        """
        node_type = "BSC"
        total_bsc_count = len(all_available_nodes.get(node_type)) if node_type in all_available_nodes else 0
        log.logger.debug("Total available BSC count : {0}".format(total_bsc_count))
        required_bsc_count = updated_requirements.get(node_type) if node_type in updated_requirements else 0
        log.logger.debug("Updated BSC allocation count : {0}".format(required_bsc_count))
        if total_bsc_count > 15 and required_bsc_count < 15:
            updated_requirements["BSC"] = 15
            profile.TOTAL_NODES = sum(updated_requirements.values())
        return updated_requirements

    @staticmethod
    def select_ne_type_available_nodes(updated_requirements, all_available_nodes):
        """
        Select the available nodes by ne type

        :param updated_requirements: Dictionary containing the updated NE type requirements
        :type updated_requirements: dict
        :param all_available_nodes: Dictionary containing all of the available nodes sorted by ne type
        :type all_available_nodes: dict

        :return: List of the available nodes
        :rtype: list
        """
        nodes = []
        for ne_type, required in sorted(updated_requirements.items(), key=lambda x: x[1]):
            if required:
                nodes.extend(all_available_nodes.get(ne_type)[:required])
        return nodes

    def correct_ne_type_under_allocation(self, ne_type_allocation_values, determined_requirements):
        """
        Checks for NeTypes under allocations and attempt correct if extra nodes are available for another NE

        :param ne_type_allocation_values: Dictionary containing the NEType, tuple under allocation/extra nodes available
        :type ne_type_allocation_values: dict
        :param determined_requirements: Dictionary containing the initially determined netype requirements
        :type determined_requirements: dict

        :return: Dictionary of the updated NEType requirements
        :rtype: dict
        """
        under_allocations = {key: value[0] for key, value in ne_type_allocation_values.items() if value[0]}
        excess_available = {key: value[1] for key, value in ne_type_allocation_values.items() if value[1]}
        if under_allocations and excess_available:
            while sum(under_allocations.values()) > 0 and sum(excess_available.values()) >= 1:
                under_allocations, determined_requirements = self.alter_allocation_dict(under_allocations,
                                                                                        determined_requirements)
                excess_available, determined_requirements = self.alter_allocation_dict(excess_available,
                                                                                       determined_requirements,
                                                                                       increase=True)
        log.logger.debug("Updated requirements\t{0}".format(determined_requirements))
        return determined_requirements

    @staticmethod
    def alter_allocation_dict(dict_to_alter, required_dict, increase=False):
        """
        Function to update the respective dictionaries tracking the under allocations, excess nodes and required nodes

        :param dict_to_alter: Dictionary tracking the under allocations or excess nodes
        :type dict_to_alter: dict
        :param required_dict: Dictionary tracking the required node allocations
        :type required_dict: dict
        :param increase: Boolean indicating if the required nodes dict should be increased or decreased
        :type increase: bool

        :return: Tuple containing the updated dictionaries
        :rtype: tuple
        """
        for key, value in dict_to_alter.items():
            if value:
                dict_to_alter[key] -= 1
                if increase:
                    required_dict[key] += 1
                else:
                    required_dict[key] -= 1
                break
        return dict_to_alter, required_dict

    def determine_if_ne_type_under_allocation(self, determined_requirements, all_available_nodes):
        """
        Check for under allocations and additional nodes

        :param determined_requirements: Dictionary containing the initial determined
        :type determined_requirements: dict
        :param all_available_nodes: Dictionary containing all of the available nodes sorted by ne type
        :type all_available_nodes: dict

        :return: Dictionary containing the NEType, tuple under allocation/extra nodes available
        :rtype: dict
        """
        ne_type_under_allocations = {}
        for ne_type, required in determined_requirements.items():
            total_ne_nodes = len([node for node in all_available_nodes.get(ne_type) if node.primary_type == ne_type])
            diff = self.validate_required_count_is_available(required, total_ne_nodes)
            excess = total_ne_nodes - required if not diff else 0
            ne_type_under_allocations[ne_type] = (diff, excess)
        log.logger.debug("NEType allocation values: [{0}]".format(ne_type_under_allocations))
        return ne_type_under_allocations

    @staticmethod
    def validate_required_count_is_available(determined_requirement, available_node_count):
        """
        Function to detect under availability of required NEType nodes

        :param determined_requirement: Total of the required node(s) for NEType
        :type determined_requirement: int
        :param available_node_count: Total of the available node(s) for NEType
        :type available_node_count: int

        :return: Difference if any in required versus available NEType nodes
        :rtype: int
        """
        diff = 0
        log.logger.debug("Checking for difference between available and required nodes by ne type.")
        if determined_requirement > available_node_count:
            diff = determined_requirement - available_node_count
        log.logger.debug("Completed check for difference between available and required nodes by ne type, difference "
                         "found: [{0}] nodes.".format(diff))
        return diff

    def get_all_available_nodes_for_supported_node_types_attribute(self, profile, ne_types, node_dict):
        """
        Function to get all available nodes for supported node types before attempting split

        :param profile: Profile instance requesting nodes
        :type profile: `lib.profile.Profile`
        :param ne_types: List of NEType strings
        :type ne_types: list
        :param node_dict: Dictionary containing the existing nodes in the pool
        :type node_dict: dict

        :return: Dictionary containing all available nodes by NEType
        :rtype: dict
        """
        profile_name = getattr(profile, 'NAME', 'Non Profile')
        log.logger.debug("Retrieving all available nodes for profile: [{0}] and NETypes: [{1}].".format(
            profile_name, ne_types))
        available_nodes = {}

        for ne_type in ne_types:
            try:
                available_nodes[ne_type] = self.get_random_available_nodes(profile, node_type=ne_type,
                                                                           node_dict=node_dict)
            except NoNodesAvailable:
                available_nodes[ne_type] = []
                log.logger.debug("No nodes of type: [{0}] available for profile: [{1}].".format(ne_type, profile_name))
                continue
        log.logger.debug("Completed retrieving all available nodes")
        return available_nodes

    def set_expected_total_nodes_by_type(self, profile, ne_types, node_dict=None):
        """
        Function to set the expected number of node for each required NEType

        :param profile: Profile instance requesting nodes
        :type profile: `lib.profile.Profile`
        :param ne_types: List of NEType strings
        :type ne_types: list
        :param node_dict: Dictionary containing the nodes in the pool
        :type node_dict: dict

        :return: Dictionary containing key, value pairs NEType and count expected.
        :rtype: dict
        """
        log.logger.debug("Setting expected total nodes by NEType.")
        profile_total_nodes = getattr(profile, 'TOTAL_NODES', 0)
        total_nodes_by_type, sum_of_total_nodes = self.calculate_total_node_values_type(ne_types, node_dict)
        ne_type_totals = {}
        for ne_type in ne_types:
            if sum_of_total_nodes:
                ne_type_totals[ne_type] = self.determine_expected_ne_type_count(profile_total_nodes,
                                                                                total_nodes_by_type.get(ne_type),
                                                                                sum_of_total_nodes)
        log.logger.debug("Completed setting expected total nodes by NEType.")
        return ne_type_totals

    def calculate_total_node_values_type(self, ne_types, node_dict=None):
        """
        Function to calculate total nodes for each NEType required and the combined total

        :param ne_types: List of NEType strings
        :type ne_types: list
        :param node_dict: Dictionary containing the nodes in the pool
        :type node_dict: dict

        :return: Dictionary containing total nodes for each NEType required and the combined total
        :rtype: tuple
        """
        log.logger.debug("Determining totals by NEType and combined total.")
        all_nodes_dict = node_dict if node_dict else self._nodes
        total_nodes_by_type = {ne_type: len(all_nodes_dict.get(ne_type)) for ne_type in ne_types if
                               ne_type in node_dict.keys()}
        sum_of_total_nodes = sum(total_nodes_by_type.values())
        log.logger.debug("Completed etermining totals by NEType and combined total.")
        return total_nodes_by_type, sum_of_total_nodes

    @staticmethod
    def determine_expected_ne_type_count(profile_total_nodes, ne_type_total, total_nodes_count):
        """
        Determine the expected ne type split based upon what is available in the pool

        :param profile_total_nodes: Total nodes required by the profile
        :type profile_total_nodes: int
        :param ne_type_total: Total nodes by NEType in the pool
        :type ne_type_total: int
        :param total_nodes_count: Total node by all required NETypes in the pool
        :type total_nodes_count: int

        :return: Number of NETypes required
        :rtype: int
        """
        return int(math.ceil(profile_total_nodes * ne_type_total / (float(total_nodes_count))))

    @staticmethod
    def _ensure_max_total_nodes(profile, total_nodes_by_type, sum_of_required_nodes):
        """"
        To shave of the extra nodes if any were added due to the math.ceil function so that exact number of
        nodes as mentioned in the network config file are fetched

        :param profile: profile to which nodes are being allocated to
        :type profile: enmutils_int.lib.profile.Profile
        :param total_nodes_by_type: list of node types and their respective count
        :type total_nodes_by_type: list
        :param sum_of_required_nodes: sum of the nodes of supported node types
        :type sum_of_required_nodes: int
        :return: list of tuples with exact number of nodes of supported types required by the profile
        :rtype: list
        """
        extra_nodes = sum_of_required_nodes - profile.TOTAL_NODES
        log.logger.debug("{0} nodes have been fetched extra than what is required for profile {1}".format(extra_nodes, profile.NAME))
        high_node_count = 0
        type_of_node = None
        for node_type, node_count in total_nodes_by_type:
            if node_count > high_node_count:
                high_node_count = node_count
                type_of_node = node_type
        if high_node_count > extra_nodes and type_of_node is not None:
            index = total_nodes_by_type.index((type_of_node, high_node_count))
            total_nodes_by_type[index] = (type_of_node, (high_node_count - extra_nodes))
        return total_nodes_by_type

    def _update_node_dict(self):
        """
        Update the the nodes dictionary based on those keys available in LoadNodeMixin

        """
        log.logger.debug("Checking for NE keys not present in the node pool dict.")
        missing_keys = set(NODE_CLASS_MAP.keys()).difference(self._nodes.keys())
        if missing_keys:
            log.logger.debug("Updating node pool dict with missing keys:: {0}.".format(", ".join(missing_keys)))
            self._nodes.update({key: [] for key in missing_keys})
        log.logger.debug("All NE keys currently included.")

    @staticmethod
    def nodes_to_be_allocated(available_nodes, profile, pre_allocated_nodes):
        """
        Select the nodes to be allocated, trigger LTE Cell Type update if needed.

        :param available_nodes: List of all currently available nodes
        :type available_nodes: list
        :param profile: Profile instance requesting the allocation
        :type profile: `enmutils_int.lib.profile.Profile`
        :param pre_allocated_nodes: List of nodes already allocated
        :type pre_allocated_nodes: list

        :return: List of nodes to be allocated
        :rtype: list
        """
        if getattr(profile, "LTE_CELL_CHECK", False):
            log.logger.debug("Updating LTE cell value before returning nodes.")
            return [update_lte_node(node) for node in available_nodes if node not in pre_allocated_nodes]
        else:
            return [node for node in available_nodes if node not in pre_allocated_nodes]


class ProfilePool(Pool):
    PERSISTENCE_KEY = 'workload_pool'

    @persist_after
    def allocate_nodes(self, profile, nodes=None):
        """
        Allocates the specified profile to the node(s)

        :param profile: the profile which will be allocated to the node
        :type profile: `enmutils_int.lib.profile.Profile`
        :param nodes: none or list of nodes that the profile will be allocated to
        :type nodes: None or list

        """
        log.logger.debug("Allocating nodes to profile: {0}".format(profile.NAME))
        if not cached_nodes_list:
            self._update_node_dict()

        if nodes:
            self.add_profile_to_profiles_attr_on_nodes(profile, nodes)
            log.logger.debug("Allocation of specific pool nodes - complete")
            return

        num_required_nodes = self.get_num_required_nodes(profile)

        if hasattr(profile, 'BATCH_MO_SIZE'):
            self.allocate_batch_by_mo(profile)
        else:
            available_nodes = nodes or self.get_available_nodes(profile)

            available_nodes = filter_bsc_nodes_based_upon_size(profile, available_nodes)
            log.logger.debug("Available nodes after BSC filtration: {0}".format(len(available_nodes)))

            available_nodes = handle_one_total_node_and_multiple_support_types(profile, available_nodes)
            log.logger.debug("Available nodes after multiple support type handling: {0}".format(len(available_nodes)))

            self.error_profile_if_node_under_allocation(num_required_nodes, len(available_nodes), profile)

            if (any([profile.NAME.startswith("SHM_"), profile.NAME.startswith("DYNAMIC_CRUD_")]) and
                    hasattr(profile, "NODES_PER_HOST")):
                available_nodes = NodesFilter(profile, available_nodes, "").execute()
                log.logger.debug("Available nodes after filtering for SHM or DYNAMIC_CRUD profiles having "
                                 "NODES_PER_HOST set: {0}".format(len(available_nodes)))

            log.logger.debug("Checking for pre-allocated nodes")
            pre_allocated_nodes = self.allocated_nodes(profile)
            log.logger.debug("Nodes pre-allocated to profile {0}: {1}".format(profile.NAME, len(pre_allocated_nodes)))
            nodes_to_be_allocated = self.nodes_to_be_allocated(available_nodes, profile, pre_allocated_nodes)
            self.add_profile_to_profiles_attr_on_nodes(profile, nodes_to_be_allocated)

            get_allocated_node_summary(profile)

        log.logger.debug("Allocate pool nodes - complete")

    @staticmethod
    def add_profile_to_profiles_attr_on_nodes(profile, nodes_to_be_allocated):
        """
        Add name of profile to profiles attribute on all nodes to be allocated

        :param profile: Profile object
        :type profile: `enmutils_int.lib.profile.Profile`
        :param nodes_to_be_allocated: list of nodes to be updated with profile
        :type nodes_to_be_allocated: list
        """
        log.logger.debug("Adding {0} profile to {1} nodes".format(profile.NAME, len(nodes_to_be_allocated)))
        error_allocating_nodes = False
        updated_nodes = dict()
        for node in nodes_to_be_allocated:
            try:
                latest_node = node.add_profile(profile)
                updated_nodes[latest_node.node_id] = latest_node
            except AddProfileToNodeError:
                error_allocating_nodes = True

        update_cached_list_of_nodes(updated_nodes)

        if error_allocating_nodes:
            profile.add_error_as_exception(AddProfileToNodeError(
                'Errors occurred when allocating the profile to the nodes. '
                'Please see {0} profile logs for more details.'.format(profile)))

        log.logger.debug("Adding profile to nodes complete")

    @staticmethod
    def get_num_required_nodes(profile):
        """
        Determine the required number of nodes based on the attributes of the profile

        :param profile: the profile which will be allocated to the node
        :type profile: enmutils_int.lib.profile.Profile object

        :return: Required number of nodes based on the attributes of the profile
        :rtype: int
        """
        log.logger.debug("Get required number of nodes based upon profile attributes.")
        if hasattr(profile, 'MAX_NODES_TO_ALLOCATE'):
            num_required_nodes = profile.MAX_NODES_TO_ALLOCATE
        elif hasattr(profile, 'TOTAL_NODES'):
            num_required_nodes = profile.TOTAL_NODES
        elif hasattr(profile, 'NODES'):
            num_required_nodes = sum(profile.NODES.values())
        else:
            num_required_nodes = sum(profile.NUM_NODES.values())
        log.logger.debug("Number of nodes required by {0} (based upon profile attributes): {1}"
                         .format(profile.NAME, num_required_nodes))
        return num_required_nodes

    def error_profile_if_node_under_allocation(self, num_required_nodes, total_available_nodes, profile):
        """
        Errors the profile if there is an under allocation of nodes

        :param num_required_nodes: Total nodes required by the profile
        :type num_required_nodes: int
        :param total_available_nodes: Total available nodes
        :type total_available_nodes: int
        :param profile: Profile object requesting the nodes
        :type profile: `Profile`
        """
        if num_required_nodes > total_available_nodes:
            error_message = ("NOTE: The total number of {2}{0}) does not match the required number of nodes ({1})."
                             "Profile will continue with available nodes."
                             .format(total_available_nodes, num_required_nodes, NOTALLNODESCMSYNCKEY))
            self.determine_if_environ_warning_to_be_added_to_profile(error_message, profile)

    def allocate_batch_by_mo(self, profile):
        """
        Function to select the appropriate Batch MO function based on the profile requirements

        :param profile: the profile which will be allocated to the node
        :type profile: enmutils_int.lib.profile.Profile object
        """

        if hasattr(profile, 'NUM_NODES'):
            log.logger.debug("Value for NUM NODES found on profile, attempting to allocate by Ne Type.")
            self.allocate_batch_by_mo_profile_using_num_nodes(profile)
        else:
            allocate_nodes_with_mos(profile)

    @staticmethod
    def sort_num_node_by_total_nodes(profile):
        """
        Sort the num nodes dictionary, if total nodes is present

        :param profile: the profile which will be allocated to the node
        :type profile: enmutils_int.lib.profile.Profile object

        :return: Ordered dictionary based on the "fill" node being last
        :rtype: dict
        """
        if hasattr(profile, "TOTAL_NODES"):
            # sort based on the value, not keys
            return OrderedDict(sorted(profile.NUM_NODES.items(), key=lambda x: x[1], reverse=True))
        return profile.NUM_NODES

    def allocate_batch_by_mo_profile_using_num_nodes(self, profile):
        """
        Function to handle NUM_NODES versus SUPPORTED_NODE_TYPES

        :param profile: the profile which will be allocated to the node
        :type profile: enmutils_int.lib.profile.Profile object
        """
        log.logger.debug("Starting allocation of nodes, by batching MOs using NUM NODES value(s).")
        node_pool_dict = self.node_dict
        profile.NUM_NODES = self.sort_num_node_by_total_nodes(profile)
        for ne_type, total_nodes in profile.NUM_NODES.iteritems():
            log.logger.debug("Attempting to allocate {} {} nodes, with MO value(s): [{}]."
                             .format(ne_type, total_nodes, profile.MO_VALUES))
            total_nodes = self.calculate_total_nodes(total_nodes, profile, ne_type, node_pool_dict)
            allocate_nodes_with_mos(profile, [ne_type], total_nodes)
        log.logger.debug("Completed allocation of nodes, by batching MOs using NUM NODES value(s).")

    @staticmethod
    def calculate_total_nodes(total_nodes, profile, ne_type, node_pool_dict):
        """
        Determine the total nodes to be batched

        :param total_nodes: Total node value extracted from the corresponding key in NUM_NODES
        :type total_nodes: int
        :param profile: the profile which will be allocated to the node
        :type profile: enmutils_int.lib.profile.Profile object
        :param ne_type: The key value of NUM_NODES representing a NE Type
        :type ne_type: str
        :param node_pool_dict: Dictionary containing all of the existing nodes in the workload pool
        :type node_pool_dict: dict

        :return: The total nodes to be batched
        :rtype: int
        """
        log.logger.debug("Calculating total nodes required for batch operation.")
        if total_nodes == -1 and not hasattr(profile, "MAX_NODES_TO_ALLOCATE"):
            # Where both TOTAL_NODES and NUM_NODES are used, the total nodes needs to adjust for any allocated nodes
            total_nodes = profile.TOTAL_NODES - len(profile.nodes_list) if hasattr(profile, "TOTAL_NODES") else len(
                node_pool_dict.get(ne_type))
            log.logger.debug("NUM NODES values set to -1, amending to total {} in pool: {}."
                             .format(ne_type, total_nodes))
        else:
            total_nodes = profile.MAX_NODES_TO_ALLOCATE
        log.logger.debug("Calculated total nodes required for batch operation.")
        return total_nodes

    @persist_after
    def deallocate_nodes(self, profile):
        """
        Deallocate the specified profile that was allocated to the node(s).

        :param profile: the profile which will be deallocated from the node(s)
        :type profile: enmutils_int.lib.profile.Profile
        """
        log.logger.debug("Deallocation of nodes")
        error_deallocating_nodes = False
        allocated_nodes = self.allocated_nodes(profile)
        if allocated_nodes:
            log.logger.debug("Removing profile from nodes")
            for node in allocated_nodes:
                try:
                    node.remove_profile(profile)
                except RemoveProfileFromNodeError:
                    error_deallocating_nodes = True
            log.logger.debug("Removing profile from nodes complete")

            if error_deallocating_nodes:
                profile.add_error_as_exception(RemoveProfileFromNodeError(
                    "Errors occurred when deallocating the profile from the nodes. Please see '{0}' profile "
                    "logs for more details.".format(profile)))

            log.logger.debug("Deallocated the profile: '{0}' from all nodes it was allocated to".format(profile))
        else:
            log.logger.debug("The profile: '{0}' is not allocated to any node".format(profile))

    def exchange_nodes(self, profile):
        """
        Given the profile, returns the currently allocated nodes to the pool and allocates new nodes to the profile

        :param profile: Profile from which the nodes are to be deallocated and then reallocated
        :type profile: enmutils_int.lib.profile.Profile
        """
        log.logger.debug("Exchanging nodes for profile '{0}'".format(profile))
        self.deallocate_nodes(profile)
        self.allocate_nodes(profile)

    @property
    def db(self):
        return persistence.default_db()


class NodesFilter(object):
    def __init__(self, item, nodes, node_type, exclude_nodes=None):
        """
        Filters nodes from a list of available nodes
        :param item: profile which looks for nodes
        :type item: enmutils_int.lib.profile.Profile
        :param nodes: list of nodes
        :type nodes: list
        :param node_type: node type
        :type node_type: str
        :param exclude_nodes: list of nodes to be excluded
        :type exclude_nodes: list
        """
        self.item = item
        self.nodes = nodes
        self.node_type = node_type
        self.exclude_nodes = exclude_nodes

    @staticmethod
    def check_node_model_presence(attr_per_node_type, node, variable):
        """
        Checks for the presence of the model identity value in a node
        :param attr_per_node_type: dict of attributes and values
        :type attr_per_node_type: dict
        :param variable: dict of attributes and values
        :type variable: dict
        :param node: Node object to check the availability as per attribute type
        :type node: enm_node.Node object
        :return: boolean value to check whether to include node includes model identity or not
        :rtype: bool
        """
        return True if getattr(node, variable, None) not in attr_per_node_type[variable] else False

    @staticmethod
    def filters_node_based_on_node_ip(attr_per_node_type, node, variable):
        """
        Checks for the presence of the ipv4/ipv6 nodes based on node_ip filter value
        node_ip filter value '.' for ipv4 and ':' for ipv6
        :param attr_per_node_type: dict of attributes and values
        :type attr_per_node_type: dict
        :param variable: Key variable which value needs to be checked for the equivalance of node ip value
        :type variable: str
        :param node: Node object to check the availability as per attribute type
        :type node: enm_node.Node object
        :return: boolean value to check whether to include node based on node_ip value
        :rtype: bool
        """
        return True if attr_per_node_type[variable] in getattr(node, variable) else False

    @staticmethod
    def check_attr_per_node_type_value_equivalence(attr_per_node_type, node, variable):
        """
        Checks for the equivalance of node attribute value and attribute value
        :param attr_per_node_type: dict of attributes and values
        :type attr_per_node_type: dict
        :param variable: Key variable which value needs to be checked for the equivalance of given variable value
        :type variable: str
        :param node: Node object to check the availability as per attribute type
        :type node: enm_node.Node object
        :return: boolean value to check whether to include node includes model identity or not
        :rtype: bool
        """
        match = False
        for value in attr_per_node_type[variable]:
            if value != getattr(node, variable, None):
                match = False
            else:
                match = True
                break
        return match

    def _filter_node_by_attr_per_each_node(self, node, attr_per_node_type):
        """
        Filters nodes on a specific attribute per specific given nodes object

        :param attr_per_node_type: dict of attributes and values
        :type attr_per_node_type: dict
        :param node: Node object to check the availability as per attribute type
        :type node: enm_node.Node object
        :return: boolean value to check whether to include node in the filtered list or not
        :rtype: bool
        """
        match = True
        for variable in attr_per_node_type:
            if hasattr(node, variable):
                if "model" in variable:
                    match = match and self.check_node_model_presence(attr_per_node_type, node, variable)
                elif "node_ip" in variable:
                    match = match and self.filters_node_based_on_node_ip(attr_per_node_type, node, variable)
                else:
                    match = match and self.check_attr_per_node_type_value_equivalence(attr_per_node_type, node, variable)
        return match

    def _filter_nodes(self, attr_per_node_type):
        """
        Filters nodes on a specific attribute on the node object
        :param attr_per_node_type: dict of attributes and values
        :type attr_per_node_type: dict
        :return: list of nodes which have all attributes in the characteristics_per_node_type dict
        :rtype: dict
        """
        filtered_nodes = []
        excluded_nodes = self.exclude_nodes if self.exclude_nodes else []
        for node in self.nodes:
            match = self._filter_node_by_attr_per_each_node(node, attr_per_node_type)

            if match and node.node_id not in excluded_nodes and node.is_available_for(self.item):
                filtered_nodes.append(node)

        if hasattr(self.item, "ME_TYPE_NODES_PERCENTAGE") and self.item.ME_TYPE_NODES_PERCENTAGE:
            log.logger.debug("ME_TYPE_NODES_PERCENTAGE : {0}".format(self.item.ME_TYPE_NODES_PERCENTAGE))
            final_nodes = group_nodes_per_me_type(filtered_nodes)
            filtered_nodes_based_on_percentage_of_metype = []
            for _me_type, _percentage in self.item.ME_TYPE_NODES_PERCENTAGE.iteritems():
                if _me_type in final_nodes:
                    metype_nodes = final_nodes[_me_type][:int(round(_percentage * (float(sum(self.item.NUM_NODES.values())) / 100)))]
                    log.logger.debug("{0} nodes found for {1}".format(len(metype_nodes), _me_type))
                    filtered_nodes_based_on_percentage_of_metype.extend(metype_nodes)

            log.logger.debug("Filtered nodes based on percentage of "
                             "metypes : {0}".format(len(filtered_nodes_based_on_percentage_of_metype)))
            return filtered_nodes_based_on_percentage_of_metype

        return filtered_nodes

    def _filter_nodes_per_netsim_host(self, nodes):
        """
        Filters nodes based on netsim hosts
        :param nodes: list of nodes
        :type nodes: list
        :return: list of filtered nodes
        :rtype: list
        """
        log.logger.debug("Filtering node allocation by netsim limitation. {0}".format(len(nodes)))
        host_dict = group_nodes_per_netsim_host(nodes)
        if hasattr(self.item, "NAME") and self.item.NAME == "SHM_27":
            nodes = self.sort_by_host_evenly(host_dict)
        else:
            nodes = []
            for key in host_dict.iterkeys():
                nodes.extend(host_dict.get(key)[0:self.item.NODES_PER_HOST])
        log.logger.debug("Completed filtering node allocation by netsim limitation. {0}".format(len(nodes)))
        return nodes

    def sort_by_host_evenly(self, host_dict):
        """
        Sort the supplied nodes, applying the nodes per host limit and ensuring an even distribution if possible

        :param host_dict: Dictionary containing nodes sorted by host
        :type host_dict: dict

        :return: list of filtered nodes
        :rtype: list
        """
        log.logger.debug("Starting sort of node types per host.")
        available_nodes = []
        host_type_dict = self._sort_by_host_and_ne_type(host_dict)
        unused = {}
        total_required_per_type = self.item.MAX_NODES / 2
        for host, ne_types in host_type_dict.items():
            if len(ne_types) == 1:
                for ne_type in ne_types.iterkeys():
                    available_nodes.extend(host_type_dict.get(host).get(ne_type)[:self.item.NODES_PER_HOST])
            else:
                unused.update({host: ne_types})
        # If there are unused nodes i.e SIU/TCU on the same box, check if we need more nodes from them
        if unused:
            available_nodes = self.fill_ne_type_requirement(unused, total_required_per_type, available_nodes)
        siu_allocated, tcu_allocated = (len([node for node in available_nodes if node.primary_type == "TCU02"]),
                                        len([node for node in available_nodes if node.primary_type == "SIU02"]))
        if len(available_nodes) < self.item.MAX_NODES:
            msg = ("Profile requires an even distribution of no more than {0} nodes per NetSim, totalling {1} nodes. "
                   "Only TCU02 nodes::  {2} SIU02 nodes:: {3}, available after applying nodes per host limit."
                   .format(self.item.NODES_PER_HOST, self.item.MAX_NODES, tcu_allocated, siu_allocated))
            log.logger.info(msg)
            self.item.add_error_as_exception(NotAllNodeTypesAvailable(msg))
        if siu_allocated and tcu_allocated and siu_allocated >= total_required_per_type <= tcu_allocated:
            nodes = ([node for node in available_nodes if node.primary_type == "TCU02"][:total_required_per_type] +
                     [node for node in available_nodes if node.primary_type == "SIU02"][:total_required_per_type])
        else:
            nodes = available_nodes[:self.item.MAX_NODES]
        log.logger.debug("Completed sorting by host evenly, returning\tTCU02 nodes:: {0}\tSIU02 nodes:: {1}, after "
                         "applying nodes per host limit.".format(tcu_allocated, siu_allocated))

        return nodes

    def fill_ne_type_requirement(self, unused_nodes, total_required_per_type, available_nodes):
        """
        Based upon the remaining dictionary of mixed simulations, reduce any under allocation of nodes

        :param unused_nodes: Dictionary containing the {host: {"netype": ["node", "node"]}
        :type unused_nodes: dict
        :param total_required_per_type: Total number of nodes per primary type required
        :type total_required_per_type: int
        :param available_nodes: List of currently selected nodes
        :type available_nodes: list

        :return: List of updated selected nodes
        :rtype: list
        """
        log.logger.debug("Starting fill of NE types available per host.")
        total_tcu = len([node for node in available_nodes if node.primary_type == "TCU02"])
        total_siu = len([node for node in available_nodes if node.primary_type == "SIU02"])
        total_per_ne_per_host = self.item.NODES_PER_HOST / 2
        siu_required, tcu_required = total_required_per_type - total_siu, total_required_per_type - total_tcu
        for host, ne_types in unused_nodes.items():
            if len(available_nodes) >= self.item.MAX_NODES:
                break
            if tcu_required and siu_required and (tcu_required + siu_required <= self.item.NODES_PER_HOST):
                siu_required, tcu_required, available_nodes = self.extend_filtered_list((siu_required, tcu_required),
                                                                                        ne_types, host, unused_nodes,
                                                                                        available_nodes)
            elif tcu_required >= total_per_ne_per_host <= siu_required:
                siu_required, tcu_required, available_nodes = self.extend_filtered_list((siu_required, tcu_required),
                                                                                        ne_types, host, unused_nodes,
                                                                                        available_nodes,
                                                                                        index=total_per_ne_per_host)
            else:
                siu_required, tcu_required, available_nodes = self.balance_siu_tcu_indexes(
                    (siu_required, tcu_required, total_per_ne_per_host), ne_types, host, unused_nodes, available_nodes)
        log.logger.debug("Completed fill of NE types available per host.")
        return available_nodes

    def balance_siu_tcu_indexes(self, under_allocation, ne_types, host, unused_nodes, available_nodes):
        """
        Determines if the TCU or SIU requirement needs to be adjusted to allocate full requirement

        :param under_allocation: Tuple containing the values related to current under allocations
        :type under_allocation: tuple
        :param ne_types: List of NE primary types
        :type ne_types: list
        :param host: Name of the netsim host to select nodes from
        :type host: str
        :param unused_nodes: Dictionary containing the {host: {"netype": ["node", "node"]}
        :type unused_nodes: dict
        :param available_nodes: List of currently selected nodes
        :type available_nodes: list

        :return: Tuple containing the updated SIU and TCU requirements, and the list of selected nodes
        :rtype: tuple
        """
        log.logger.debug("Updating currently selected nodes.")
        siu_required, tcu_required, total_per_ne_per_host = under_allocation
        tcu_needed = tcu_required if tcu_required < total_per_ne_per_host else self.item.NODES_PER_HOST - siu_required
        siu_needed = siu_required if siu_required < total_per_ne_per_host else self.item.NODES_PER_HOST - tcu_required
        for ne_type in ne_types:
            if ne_type == "SIU02":
                index = siu_needed
            else:
                index = tcu_needed
            _, _, available_nodes = self.extend_filtered_list(
                (siu_required, tcu_required), [ne_type], host, unused_nodes, available_nodes, index=index)
        log.logger.debug("Completed updating currently selected nodes.")
        return siu_required - siu_needed, tcu_required - tcu_needed, available_nodes

    @staticmethod
    def extend_filtered_list(under_allocation, ne_types, host, unused_nodes, available_nodes, index=None):
        """
        Based upon the inputs extend the current list of nodes by the supplied dict and index value

        :param under_allocation: Tuple containing the values related to current under allocations
        :type under_allocation: tuple
        :param ne_types: List of NE primary types
        :type ne_types: list
        :param host: Name of the netsim host to select nodes from
        :type host: str
        :param unused_nodes: Dictionary containing the {host: {"netype": ["node", "node"]}
        :type unused_nodes: dict
        :param available_nodes: List of currently selected nodes
        :type available_nodes: list
        :param index: Index value to be selected
        :type index: int

        :return: Tuple containing the updated SIU and TCU requirements, and the list of selected nodes
        :rtype: tuple
        """
        siu_required, tcu_required = under_allocation
        for ne_type in ne_types:
            updated_index = index if index else siu_required if ne_type == "SIU02" else tcu_required
            available_nodes.extend(unused_nodes.get(host).get(ne_type)[:updated_index])
            if index and ne_type == "SIU02":
                siu_required -= updated_index
            elif index and ne_type == "TCU02":
                tcu_required -= updated_index
        if not index:
            siu_required, tcu_required = 0, 0

        return siu_required if siu_required >= 0 else 0, tcu_required if tcu_required >= 0 else 0, available_nodes

    @staticmethod
    def _sort_by_host_and_ne_type(grouped_nodes):
        """
        Sort nodes by host and then by primary type

        :param grouped_nodes: Dictionary containing nodes sorted by host
        :type grouped_nodes: dict

        :return: Dictionary of nodes sorted by host and then by primary type
        :rtype: dict
        """
        log.logger.debug("Sorting grouped nodes by host, primary type and nodes.")
        host_type_dict = {}
        for host, nodes in grouped_nodes.items():
            host_type_dict[host] = {}
            for node in nodes:
                if node.primary_type not in host_type_dict[host]:
                    host_type_dict[node.netsim][node.primary_type] = []
                host_type_dict[host][node.primary_type].append(node)
        log.logger.debug("Completed sorting grouped nodes by host, primary type and nodes.")
        return host_type_dict

    @staticmethod
    def _retain_pre_allocated_nodes(nodes, pre_allocated_nodes):
        """
        Keeps nodes which were already allocated by the user

        :param nodes: list of nodes
        :type nodes: list
        :param pre_allocated_nodes: list of pre allocated nodes
        :type pre_allocated_nodes: list
        :return: list of pre allocated nodes
        :rtype: list
        """

        unique_available_nodes = list(set(nodes).difference(set(pre_allocated_nodes)))
        random.shuffle(unique_available_nodes)
        pre_allocated_nodes.extend(unique_available_nodes)

        return pre_allocated_nodes

    def execute(self):
        """
        Executes the filter returning list of filtered nodes
        :return: list of nodes
        :rtype: list
        """

        nodes = []
        pre_allocated_nodes = []
        if hasattr(self.item, "NODE_FILTER") and self.node_type in self.item.NODE_FILTER:
            attrs = self.item.NODE_FILTER
            for node_type in attrs.keys():
                nodes += self._filter_nodes(attrs[node_type])
        else:
            nodes = [node for node in self.nodes if node.is_available_for(self.item)]
        if hasattr(self.item, 'NAME'):
            pre_allocated_nodes = [node for node in nodes if node.is_pre_allocated_to_profile(self.item)]
        if pre_allocated_nodes:
            nodes = self._retain_pre_allocated_nodes(nodes, pre_allocated_nodes)
        else:
            random.shuffle(nodes)

        if getattr(self.item, "NODES_PER_HOST", None):
            nodes = self._filter_nodes_per_netsim_host(nodes)

        return nodes


def get_allocated_node_summary(profile):
    """
    Log the summary of the number of nodes and node types allocated to the profile

    :raises NoNodesAvailable: raised if there are no nodes allocated

    :param profile: profile object
    :type profile: enmutils_int.lib.profile.Profile
    """
    log.logger.debug("Printing summary of allocated nodes")
    allocated_nodes = get_pool().allocated_nodes(profile)
    if not allocated_nodes:
        raise NoNodesAvailable('No available nodes for item {0}.'.format(str(profile)))
    profile.num_nodes = len(allocated_nodes)

    node_summary = {}
    for node in allocated_nodes:
        if node.primary_type in node_summary:
            node_summary[node.primary_type] += 1
        else:
            node_summary[node.primary_type] = 1

    log.logger.debug('Allocated the following {0} nodes to profile {1}: {2}'
                     .format(len(allocated_nodes), str(profile), node_summary))


def group_nodes_per_netsim_host(nodes):
    """
    Groups the given nodes based on the host of the simulations

    :type nodes: list
    :param nodes: list of nodes

    :rtype: dict
    :return: dict of Hosts, and their corresponding nodes
    """
    host_dict = {}
    for node in nodes:
        if node.netsim not in host_dict:
            host_dict[node.netsim] = []
        host_dict.get(node.netsim).append(node)

    return host_dict


def distribute_nodes(nodes, num_nodes):
    """
    Distribute the given nodes as best we can to return the required number of nodes

    :type nodes: list
    :param nodes: List of `enm_node.Node` objects
    :type num_nodes: int
    :param num_nodes: Number of nodes required by the requesting item

    :rtype: list
    :return: list of nodes
    """
    if len(nodes) <= num_nodes:
        return nodes
    host_dict = group_nodes_per_netsim_host(nodes)
    assigned_nodes = []
    while not len(assigned_nodes) == num_nodes:
        for key in host_dict.iterkeys():
            if host_dict.get(key):
                assigned_nodes.append(host_dict.get(key).pop())
                if len(assigned_nodes) == num_nodes:
                    break

    return assigned_nodes


def get_node_mos_fdns_and_attrs(user, nodes, profile, mos_dict, attrs=None):
    """
    Get the FDN information and build MOAttr object as required

    :param user: user to execute ENM requests
    :type user: enm_user_2.User object
    :param mos_dict: dictionary with the name and required attributes of MOs
    :type mos_dict: dict
    :param nodes: list of nodes to be queried
    :type nodes: list
    :param profile: Profile instance which will generate the load
    :type profile: `Profile`
    :param attrs: dictionary with MOs as keys and a list of the MO attributes as values
    :type attrs: None or dict

    :raises ScriptEngineResponseValidationError: raised if MOs cannot be retrieved from ENM

    :return: Tuple containing the FDN output, and MOAttrs object(s) if required
    :rtype: tuple
    """
    if profile.NAME == "CMIMPORT_35":
        mos_dict = {'"asymmetric-key$$cmp"': 1, 'EUtranFreqRelation': 1536, 'ExternalGNBCUCPFunction': 512,
                    'NRCellCU': 512, 'NRFreqRelation': 2560}
        attrs = {'"asymmetric-key$$cmp"': ['renewal-mode'],
                 'EUtranFreqRelation': ['presenceAntennaPort1'],
                 'ExternalGNBCUCPFunction': ['isRemoveAllowed'],
                 'NRCellCU': ['transmitSib2'], 'NRFreqRelation': ['mdtMeasOn']}
    log.logger.debug("Querying ENM for node MO information, and attribute information if required.")
    nodes_identifier = ';'.join(node.node_id for node in nodes)
    response = user.enm_execute(
        'cmedit get {nodes_identifier} {mo_name}'.format(mo_name=';'.join(mos_dict), nodes_identifier=nodes_identifier))
    output = response.get_output()
    if output and any(["GeranCell" in _ for _ in output]):
        output = remove_gerancell_in_range(output)
    if attrs:
        attrs = MoAttrs(user=user, nodes=nodes, mos_attrs=attrs).fetch()
    if not output:
        raise ScriptEngineResponseValidationError('Cannot get MOs with name {0} from ENM'.format(','.join(mos_dict)),
                                                  response=response)
    log.logger.debug("Completed querying ENM for node MO information, and attribute information if required.")
    return output, attrs


def get_nodes_mos(user, mos_dict, nodes, profile, match_number_mos='exact', attrs=None, ignore_mo_val='new'):
    """
    Filter nodes to find only nodes that have the MOs required

    :param user: user to execute ENM requests
    :type user: enm_user2.User object
    :param mos_dict: dictionary with the name and required attributes of MOs
    :type mos_dict: dict
    :param nodes: list of nodes to be queried
    :type nodes: list
    :param profile: Profile instance which will generate the load
    :type profile: `Profile`
    :param match_number_mos: string to filter MOs count - valid values are 'exact', 'some', 'any'
                            'any' will try to match any count of MOs given
                            'some' will try to find any of the MOs regardless of number (but all MOs must be there on a node)
                            'exact' will match exact number of MOs
    :type match_number_mos: str
    :param attrs: dictionary with MOs as keys and a list of the MO attributes as values
    :type attrs: None or dict
    :param ignore_mo_val: if the MO value found is equal to this value then ignore the MO value
    :type ignore_mo_val: str

    :return:  list of nodes with needed MOs
    :rtype: list
    :raises ScriptEngineResponseValidationError: raised if MOs cannot be retrieved from ENM
    """
    nodes_mos = defaultdict(dict)
    output, attrs = get_node_mos_fdns_and_attrs(user, nodes, profile, mos_dict, attrs=attrs)
    mos_count = defaultdict(dict)
    ignored_patterns = ["EUtranFreqRelation=E", "CMSYNC", "CELLMGT"]
    for node_entry in output:
        if 'FDN' not in node_entry or any([_ in node_entry for _ in ignored_patterns]):
            continue
        mo_attrs = attrs[node_entry] if attrs else None
        fdn = node_entry.strip('FDN : ')
        node_entries = fdn.split(',')
        node_vals = [tuple(entry.split('=')) for entry in node_entries]
        tree, leaf = node_vals[:-1], node_vals[-1]
        mo_key, mo_value = leaf
        if tree[0][0] != 'SubNetwork' or mo_value == ignore_mo_val:
            continue
        first_subnetwork_index = max(_ + 1 for _, val in enumerate(tree) if "SubNetwork" in val)
        first_mo = tree[first_subnetwork_index][1]
        mo_count = mos_count[first_mo].setdefault(mo_key, 0)
        if mo_count + 1 > mos_dict.get(mo_key) and match_number_mos == 'exact':
            # We have got the number of MOs required, don't take anymore for this node
            continue
        mos_count[first_mo][mo_key] = mo_count + 1
        # First MO (most probably Subnetwork)
        next_element = nodes_mos[tree[first_subnetwork_index]]
        # Iterate over the remaining MOs up to leaf's parent element (second last in list)
        for val in tree[first_subnetwork_index + 1:]:
            next_element = next_element.setdefault(val, {})
        enm_mo = EnmMo(mo_key, mo_value, fdn, attrs=mo_attrs, is_leaf=True, user=user)
        next_element.setdefault(mo_key, []).append(enm_mo)
    filtered_nodes = []
    for node_obj in nodes:
        filtered_nodes.extend(get_filtered_nodes(node_obj, match_number_mos, mos_dict, mos_count, nodes_mos))
    return filtered_nodes


def get_filtered_nodes(node_obj, match_number_mos, mos_dict, mos_count, nodes_mos):
    """
    Update node MOs if the required number is not yet met

    :param node_obj: Node instance to be added
    :type node_obj: `load_node.LoadNode`
    :param match_number_mos: Matching condition :: exact, any, some
    :type match_number_mos: str
    :param mos_dict: Dictionary of the required MOs and the number required
    :type mos_dict: dict
    :param mos_count: Dictionary of the count of MOs found, by node id
    :type mos_count: dict
    :param nodes_mos: Dictionary containing dictionaries mapped from node to the MO paths
    :type nodes_mos: dict

    :return: List of the
    :rtype: list
    """
    nodes_found = []
    add_node = True
    node_key = (node_obj.ROOT_ELEMENT if node_obj.managed_element_type != "GNodeB" else "MeContext", node_obj.node_id)
    if match_number_mos == 'exact':
        if not mos_count[node_obj.node_id] == mos_dict:
            add_node = False
    elif match_number_mos == 'some':
        for mo_key in mos_dict:
            if mo_key not in mos_count[node_obj.node_id]:
                add_node = False
    if add_node:
        node_obj.mos = {node_key: nodes_mos[node_key]}
        nodes_found.append(node_obj)
    return nodes_found


def remove_gerancell_in_range(output, start_range=0, end_range=101):
    """
    Remove the specified range of GeranCell IDs

    :param output: List of GeranCell FDNs
    :type output: list list
    :param start_range: Lower limit of the ID range to remove
    :type start_range: int
    :param end_range: Upper limit of the ID range to remove
    :type end_range: int

    :return: List of filtered GeranCell FDNs
    :rtype: list
    """
    log.logger.debug("Remove reserved range of GeranCells if present.")
    for line in output[:]:
        if "GeranCell" in line:
            cell_id = line.split("GeranCell=")[-1].split(",")[0].encode('utf-8').strip()
            # Check if the id contains characters, the agreed range of IDs does not
            if cell_id.isdigit() and any(int(cell_id) == _ for _ in range(start_range, end_range)):
                output.remove(line)
    log.logger.debug("Successfuly removed reservered range of GeranCells if present.")
    return output


def determine_if_mixed_nodes_mos(user, mo_dict, nodes, profile, attrs=None):
    """
    Determine if the batch mos function needs to switch between node types

    :param user: User who perform the ENM query
    :type user: `enm_user_2.User`
    :param mo_dict: Dictionary containing the MOs and count to be imported
    :type mo_dict: dict
    :param nodes: List of `enm_node.BaseNode` instances
    :type nodes: list
    :param profile: Profile instance which will generate the load
    :type profile: `Profile`
    :param attrs: Dictionary containing the attributes(if any) to be updated
    :type attrs: dict

    :return: List of nodes with the required MOs/Attrs
    :rtype: list
    """
    if not hasattr(profile, "MAPPING_FOR_5G_NODE_MO"):
        return get_nodes_mos(user, mo_dict, nodes=nodes, profile=profile, attrs=attrs)
    else:
        return get_mixed_nodes_mos(user, mo_dict, nodes, profile, attrs=attrs)


def get_mixed_nodes_mos(user, mo_dict, nodes, profile, attrs=None):
    """
    Get the list of the matching nodes based upon the mix of nodes provided

    :param user: User who perform the ENM query
    :type user: `enm_user_2.User`
    :param mo_dict: Dictionary containing the MOs and count to be imported
    :type mo_dict: dict
    :param nodes: List of `enm_node.BaseNode` instances
    :type nodes: list
    :param profile: Profile instance which will generate the load
    :type profile: `Profile`
    :param attrs: Dictionary containing the attributes(if any) to be updated
    :type attrs: dict

    :return: List of nodes with the required MOs/Attrs
    :rtype: list
    """
    g_node_mo_dict, g_node_mo_attrs = {}, None
    matched_nodes, node_lists = [], []
    g_node_b_nodes = [node for node in nodes if node.managed_element_type == "GNodeB"]
    if g_node_b_nodes:
        g_node_mo_dict, g_node_mo_attrs = create_gnodeb_mo_dict_and_attrs(mo_dict, attrs, profile)
    for _ in [g_node_b_nodes, list(set(nodes).difference(g_node_b_nodes))]:
        if _:
            node_lists.append(_)
    for node_list in node_lists:
        try:
            mo_dict_for_query = g_node_mo_dict if g_node_mo_dict and node_list is g_node_b_nodes else mo_dict
            attrs_for_query = g_node_mo_attrs if g_node_mo_attrs and node_list is g_node_b_nodes else attrs
            matched_nodes.extend(get_nodes_mos(user, mo_dict_for_query, nodes=node_list, profile=profile, attrs=attrs_for_query))
        except Exception as e:
            log.logger.debug(str(e))
    return matched_nodes


def create_gnodeb_mo_dict_and_attrs(mo_dict, attrs, profile):
    """
    Create an mo_dict and attr dict for the 5G MO based upon the LTE values

    :param mo_dict: Dictionary containing the MOs and count to be imported
    :type mo_dict: dict
    :param attrs: Dictionary containing the attributes(if any) to be updated
    :type attrs: dict
    :param profile: Profile instance which will generate the load
    :type profile: `Profile`

    :return: Tuple containing the 5G mo_dict and attrs
    :rtype: tuple
    """
    g_node_mo_dict = {}
    for key in mo_dict.keys():
        if profile.MAPPING_FOR_5G_NODE_MO.get(key):
            g_node_mo_dict.update(profile.MAPPING_FOR_5G_NODE_MO.get(key))
    if attrs:
        g_node_mo_attrs = {}
        for key in g_node_mo_dict.keys():
            g_node_mo_attrs[key] = profile.MAPPING_FOR_5G_NODE_ATTRS.get(key)
    else:
        g_node_mo_attrs = None
    return g_node_mo_dict, g_node_mo_attrs


def get_batch_nodes_with_mos(profile, mo_dict, nodes, batch_size=160, user=None, attrs=None, **kwargs):
    """
    Get nodes with MOs in batches

    :param profile: profile to find nodes with MOs for
    :type profile: profile.Profile object
    :param mo_dict: dictionary with the name of MO and number of MOs needed
    :type mo_dict: dict
    :param nodes: list of enm_node.Node objects
    :type nodes: list
    :param batch_size: the number of nodes to check for MOs at a time
    :type batch_size: int
    :param user: user to execute ENM requests
    :type user: enm_user_2.User object
    :param attrs: dictionary with MOs as keys and a list of the MO attributes as values. Example use case: used when
                  creating MOs when it is mandatory to supply certain attributes for the MO creation
                  e.g. {'EUtranCellRelation': ['EUtranCellRelationId', 'neighborCellRef']}
    :type attrs: dict
    :param kwargs: Python builtin dictionary
    :type kwargs: dict

    :return: dictionary with nodes and their corresponding MOs
    :rtype: dict

    :raises NoNodesAvailable: raised if nodes with MOs cannot be found
    """
    fail_on_empty_response = kwargs.pop('fail_on_empty_response', False)
    allocate = kwargs.pop('allocate', False)
    timeout_mins = kwargs.pop('timeout_mins', 30)
    num_nodes_needed = kwargs.pop('num_nodes_needed', 100)

    user = user or get_workload_admin_user()
    if batch_size > len(nodes):
        batch_size = len(nodes)

    timeout = (datetime.datetime.now() + datetime.timedelta(minutes=timeout_mins))
    start = 0
    nodes_with_mos = []
    while start < len(nodes):
        start_time = datetime.datetime.now()
        mo_values = (mo_dict, attrs, profile)
        timeout_values = (timeout, timeout_mins, start_time)
        try:
            nodes_with_mos.extend(get_mos_and_allocate_nodes(timeout_values, user, mo_values,
                                                             nodes[start:start + batch_size], nodes_with_mos,
                                                             num_nodes_needed, allocate))
        except TimeOutError:
            return nodes_with_mos[0:num_nodes_needed]
        start += batch_size
        num_nodes_found = len(nodes_with_mos)
        if num_nodes_found >= num_nodes_needed:
            return nodes_with_mos[0:num_nodes_needed]

    if fail_on_empty_response:
        raise NoNodesAvailable("Cannot find number of nodes required: '{0}' with mos: '{1}'. "
                               "Total nodes searched: {2}.".format(num_nodes_needed, mo_dict, start))
    return nodes_with_mos[0:num_nodes_needed]


def get_mos_and_allocate_nodes(timeout_values, user, mo_values, nodes, nodes_with_mos, num_nodes_needed, allocate):
    """
    Allocate nodes if nodes contain require MOs

    :param timeout_values: Tuple containing the timeout and timeout in minutes values, and the start time
    :type timeout_values: tuple
    :param user: User who will query ENM
    :type user: `enm_user_2.User`
    :param mo_values: Tuple containing the mo_dict, attrs and profile
    :type mo_values: tuple
    :param nodes: List of `enm_node.BaseNode` instances
    :type nodes: list
    :param nodes_with_mos: List of `enm_node.BaseNode` instances with the required MOs
    :type nodes_with_mos: list
    :param num_nodes_needed: Number of nodes required
    :type num_nodes_needed: int
    :param allocate: Boolean indicating if the nodes should be allocated to the profile
    :type allocate: bool

    :raises TimeOutError: raised if timeout is reached when searching for MOs

    :return: List of `enm_node.BaseNode` instances with the required MOs
    :rtype: list
    """

    mo_dict, attrs, profile = mo_values
    timeout, timeout_mins, start_time = timeout_values
    allocated_nodes = []
    if start_time < timeout:
        try:
            nodes_list = determine_if_mixed_nodes_mos(user, mo_dict, nodes=nodes, attrs=attrs, profile=profile)
        except (ScriptEngineResponseValidationError, NoOuputFromScriptEngineResponseError) as e:
            log.logger.debug(str(e))
        else:
            updated_nodes = dict()
            for node in nodes_list:
                if (len(nodes_with_mos) + len(allocated_nodes) < num_nodes_needed and
                        node.is_available_for(profile) and allocate):
                    allocated_nodes.append(allocate_batch_mo_node(node, profile))
                    updated_nodes[node.node_id] = node
            update_cached_list_of_nodes(updated_nodes)
            return allocated_nodes
    else:
        raise TimeOutError("Max time for MO search reached. Timeout : {0} mins".format(timeout_mins))


def allocate_batch_mo_node(node, profile):
    """
    Allocate the profile to the supplied node.

    :param node: Load node object to allocate the profile to
    :type node: `load_node.LoadNodeMixin`
    :param profile: Profile object to be allocated to the node instance
    :type profile: `profile.Profile`

    :return:List of `enm_node.BaseNode` instances with the required MOs
    :rtype: list
    """
    try:
        node.add_profile(profile)
    except AddProfileToNodeError:
        pass
    return node


def update_cached_list_of_nodes(updated_nodes):
    """
    Update cached nodes list with latest version of the node object

    :param updated_nodes: dict of nodes given by node_id
    :type updated_nodes: dict
    """
    global cached_nodes_list
    if cached_nodes_list and updated_nodes:
        log.logger.debug("Updating cached list of nodes")
        cached_nodes_info = {node.node_id: index for index, node in enumerate(cached_nodes_list)}
        cached_nodes_info_keys = cached_nodes_info.keys()

        added, updated = 0, 0
        for node_id in updated_nodes.keys():
            if node_id in cached_nodes_info_keys:
                index_of_existing_node = cached_nodes_info[node_id]
                cached_nodes_list[index_of_existing_node] = updated_nodes[node_id]
                updated += 1
            else:
                cached_nodes_list.append(updated_nodes[node_id])
                added += 1
        log.logger.debug("Cache nodes: {0} (Total) {1} (Updated) {2} (Added)"
                         .format(len(cached_nodes_list), updated, added))


def allocate_nodes_with_mos(profile, supported_ne_types=None, total_nodes=None):
    """

    Allocates nodes to profiles that require nodes with specific MOs. These nodes with MOs are then persisted for later
    use by the profile if the profile is a CMImport profile.

    :param profile: profile to be allocated nodes with required MOs
    :type profile: enumtils_int.lib.profile.Profile
    :param supported_ne_types: List of specific ne types to allocate with the required MO
    :type supported_ne_types: list
    :param total_nodes: Total number of nodes required
    :type total_nodes: int

    :raises NoNodesAvailable: raised if no nodes with MOs are found
    """

    nodes_with_mos = []
    nodes = []
    attrs = profile.MOS_ATTRS if hasattr(profile, 'MOS_ATTRS') else None
    mo_values = profile.MO_VALUES if hasattr(profile, 'MO_VALUES') else None
    node_types = supported_ne_types if supported_ne_types else profile.SUPPORTED_NODE_TYPES
    total_nodes = profile.MAX_NODES_TO_ALLOCATE if hasattr(profile, 'MAX_NODES_TO_ALLOCATE') else total_nodes if total_nodes else profile.TOTAL_NODES

    for node_type in node_types:
        nodes += get_random_available_nodes(profile, node_type=node_type)
        nodes = filter_bsc_nodes_based_upon_size(profile, nodes)

    mo_values, attrs = check_for_pcg_version(profile, nodes, mo_values, attrs)

    if nodes:
        if total_nodes > len(nodes):
            profile.add_error_as_exception(NotAllNodeTypesAvailable(
                'NOTE: The total number of nodes available ({0}) does not match the required number of nodes ({1}).'
                'Profile will continue with available nodes.'.format(len(nodes), total_nodes)))
        try:
            nodes_with_mos = get_batch_nodes_with_mos(profile=profile, mo_dict=mo_values, nodes=nodes,
                                                      batch_size=profile.BATCH_MO_SIZE, num_nodes_needed=total_nodes,
                                                      attrs=attrs, timeout_mins=120, allocate=True,
                                                      fail_on_empty_response=False)
        except (ScriptEngineResponseValidationError, TimeOutError) as e:
            log.logger.info(log.red_text('Failed to find nodes with MO, response: %s' % e.message))

    if nodes_with_mos:
        set_to_persistence(profile, nodes_with_mos, mo_values, attrs)
        get_allocated_node_summary(profile)

    if not nodes_with_mos:
        raise NoNodesAvailable('Not enough required nodes [{3}]: {0} with MOs required: {1}, for profile {2}. '
                               .format(total_nodes, mo_values, str(profile), node_types))


def set_to_persistence(profile, nodes_with_mos, mo_values, attrs):
    """
    Set values to persistence for cmimport profile.

    :param profile: profile to be allocated nodes with required MOs
    :type profile: enmutils_int.lib.profile.Profile
    :param nodes_with_mos: List of filtered nodes allocated to the profile
    :type nodes_with_mos: list
    :param mo_values: dictionary with the name and required attributes of MOs
    :type mo_values: dict
    :param attrs: dictionary with MOs as keys and a list of the MO attributes as values
    :type attrs: None or dict

    """

    if profile.NAME.startswith('CMIMPORT'):
        with mutexer.mutex('cmimport-mos'):
            persistence.set(DB_KEY % profile.NAME, {n.node_id: n.mos for n in nodes_with_mos}, -1)
    if profile.NAME.startswith('CMIMPORT_25'):
        check_fetch_set_mos_to_persistence(profile, nodes_with_mos, mo_values, attrs)


def check_fetch_set_mos_to_persistence(profile, nodes, mo_values, attrs, user=None):
    """

    Fetch the value from persistence and check MOs attributes are present or not. If Mos not present then it will fetch
    from ENM and persisted for later use by the profile if the profile is a CMImport profile.

    :param profile: profile to be allocated nodes with required MOs
    :type profile: enmutils_int.lib.profile.Profile
    :param nodes: List of filtered nodes allocated to the profile
    :type nodes: list
    :param mo_values: dictionary with the name and required attributes of MOs
    :type mo_values: dict
    :param attrs: dictionary with MOs as keys and a list of the MO attributes as values
    :type attrs: None or dict
    :param user: user to execute ENM requests
    :type user: enm_user_2.User object

    """

    db_output = persistence.get(DB_KEY % profile.NAME)
    detect_mos = []
    for value in db_output.values():
        node_attr = value
        for value in node_attr.values():
            mos_attr = value
            detect_mos.append(len(mos_attr))

    if sum(detect_mos) == 0:
        user = user or get_workload_admin_user()
        mos_dict_to_set = fetch_and_build_mos_dict(user, nodes, mo_values, profile, attrs)
        with mutexer.mutex('cmimport-mos'):
            persistence.set(DB_KEY % profile.NAME, mos_dict_to_set, -1)
    else:
        log.logger.debug("Some of the MOs attributes are present in persistence.")


def fetch_and_build_mos_dict(user, nodes, mo_values, profile, attrs=None, ignore_mo_val='new', match_number_mos='exact'):
    """

    Fetch MOs details as output using cmedit and build a dictionary with nodes and MOs that will persisted later

    :param user: user to execute ENM requests
    :type user: enm_user2.User object
    :param mo_values: dictionary with the name and required attributes of MOs
    :type mo_values: dict
    :param nodes: list of nodes to be queried
    :type nodes: list
    :param profile: Profile instance which will generate the load
    :type profile: `Profile`
    :param attrs: dictionary with MOs as keys and a list of the MO attributes as values
    :type attrs: None or dict
    :param match_number_mos: string to filter MOs count - valid values are 'exact', 'some', 'any'
                            'any' will try to match any count of MOs given
                            'some' will try to find any of the MOs regardless of number (but all MOs must be there on a node)
                            'exact' will match exact number of MOs
    :type match_number_mos: str
    :param ignore_mo_val: if the MO value found is equal to this value then ignore the MO value
    :type ignore_mo_val: str
    :return:  dict of nodes with needed MOs
    :rtype: dict

    :raises ScriptEngineResponseValidationError: raised if MOs cannot be retrieved from ENM
    """
    log.logger.debug("Fetching MOs from ENM using CMEDIT command and building MOs dict")
    nodes_mos = defaultdict(dict)
    output, attrs = get_node_mos_fdns_and_attrs(user, nodes, profile, mo_values, attrs=attrs)
    mos_count = defaultdict(dict)
    ignored_patterns = ["EUtranFreqRelation=E", "CMSYNC", "CELLMGT"]
    mos_dict_to_set = {}
    for node_entry in output:
        if 'FDN' not in node_entry or any([_ in node_entry for _ in ignored_patterns]):
            continue
        mo_attrs = attrs[node_entry] if attrs else None
        fdn = node_entry.strip('FDN : ')
        node_entries = fdn.split(',')
        node_vals = [tuple(entry.split('=')) for entry in node_entries]
        tree, leaf = node_vals[:-1], node_vals[-1]
        mo_key, mo_value = leaf
        if tree[0][0] != 'SubNetwork' or mo_value == ignore_mo_val:
            continue
        first_subnetwork_index = max(_ + 1 for _, val in enumerate(tree) if "SubNetwork" in val)
        first_mo = tree[first_subnetwork_index][1]
        mo_count = mos_count[first_mo].setdefault(mo_key, 0)
        if mo_count + 1 > mo_values.get(mo_key) and match_number_mos == 'exact':
            # We have got the number of MOs required, don't take anymore for this node
            continue
        mos_count[first_mo][mo_key] = mo_count + 1
        # First MO (most probably Subnetwork)
        next_element = nodes_mos[tree[first_subnetwork_index]]
        # Iterate over the remaining MOs up to leaf's parent element (second last in list)
        for val in tree[first_subnetwork_index + 1:]:
            next_element = next_element.setdefault(val, {})
            match_value = next_element.keys()
            mos_dict_to_set = build_mos_dict(tree, match_value, next_element, mos_dict_to_set)
        enm_mo = EnmMo(mo_key, mo_value, fdn, attrs=mo_attrs, is_leaf=True, user=user)
        next_element.setdefault(mo_key, []).append(enm_mo)

    return mos_dict_to_set


def build_mos_dict(tree, match_value, next_element, mos_dict_to_set):
    """
    Build MOS dictionary to be set on persistence

    :param tree: structure of FDN in the form of list of tuple
    :type tree: list of tuple
    :param match_value: value to be matched in tree structure
    :type match_value: list
    :param next_element: nested dict of mos structure
    :type next_element: dict
    :param mos_dict_to_set: final nested dict of mos structure to set in persistence
    :type mos_dict_to_set: dict
    :return:  dict of nodes with needed MOs
    :rtype: dict

    """
    attribute_to_include = {}
    if tree[5] in match_value:
        attribute_to_include[tree[4]] = next_element
        mos_dict_to_set[tree[4][1]] = attribute_to_include

    return mos_dict_to_set


def check_for_pcg_version(profile, nodes, mo_values, attrs):
    """
    Based on PCG version sets the MO values and attributes.

    :param profile: profile to be allocated nodes with required MOs
    :type profile: enumtils_int.lib.profile.Profile
    :param nodes: List of node objects
    :type nodes: list
    :param mo_values: MO values of the respective profile
    :type mo_values: dict
    :param attrs: Attributes of the respective profile
    :type attrs: dict

    :return: The dictionary of MO values of profile object
    :rtype: dict
    :return: The dictionary of attributes of profile object
    :rtype: dict
    """
    if profile.NAME == "CMIMPORT_26":
        for node in nodes:
            if float((node.node_version).replace('-', '.')) >= 1.17:
                mo_values = profile.MO_VALUES_NEW
                attrs = profile.MOS_ATTRS_NEW
                profile.NEW_VERSION = True
                break
    return mo_values, attrs


def individually_allocate_node_to_profile(profile_name, node):
    """
    Adds the profile to node if not already added

    :param profile_name: Name of the profile to allocated nodes to
    :type profile_name: str
    :param node: LoadNode object to update with the profile
    :type node: `load_node.LoadNode`
    """
    with mutex():
        log.logger.debug("Retrieving workload pool from redis.")
        pool = get_pool()
        log.logger.debug("Allocating {} to {} if not already allocated.".format(profile_name, node.node_id))
        if profile_name not in node.profiles:
            node.profiles.append(profile_name)
            node._persist()
            pool.persist()


def generate_cell_dict(key):
    """
    Generate a dictionary of the currently created LTE and Geran nodes based upon MOs

    :param key: Identifier of the required key to be set in persistence
    :type key: str

    :return: Dictionary of node names sorted by EUtranCell and GeranCell type
    :rtype: dict
    """
    cmd = ("cmedit get * GeranCell -ne=BSC" if key in ["GSM_KEYS"]
           else "cmedit get * EUtranCellFDD;EUtranCellTDD")
    mo_dict = {"FDD": set(), "TDD": set(), "LARGE_BSC": set(), "SMALL_BSC": set(), "BSC_250_CELL": set()}
    try:
        user = get_workload_admin_user()
        response = user.enm_execute(cmd)
        if response.get_output():
            mo_list = [line for line in response.get_output() if "FDN" in line]
            grouped_mos_dict = network_mo_info.group_mos_by_node(mo_list)
            for key, values in grouped_mos_dict.iteritems():
                if any(_ for _ in values if "TDD" in _):
                    mo_dict["TDD"].add(key)
                elif any(_ for _ in values if "GeranCell" in _) and len(values) >= 2000:
                    mo_dict["LARGE_BSC"].add(key)
                elif any(_ for _ in values if "GeranCell" in _) and len(values) < 500:
                    mo_dict = sort_small_bsc_nodes(mo_dict, key, len(values))
                elif any(_ for _ in values if "FDD" in _):
                    mo_dict["FDD"].add(key)
        return mo_dict
    except Exception as e:
        log.logger.debug("Failed to retrieve list of cells from ENM, response: {0}".format(str(e)))
        return mo_dict


def sort_small_bsc_nodes(mo_dict, key, total_cells):
    """
    Further sort the "Small" bsc nodes into those with specifically 250 cells

    :param mo_dict: Dictionary of the sorted node ids
    :type mo_dict: dict
    :param key: Node id of the node
    :type key: str
    :param total_cells: Total number of cells on the BSC node
    :type total_cells: int

    :return: The updated dictionary of the sorted node ids
    :rtype: dict
    """
    if total_cells == 250:
        mo_dict["BSC_250_CELL"].add(key)
    mo_dict["SMALL_BSC"].add(key)
    return mo_dict


def filter_bsc_nodes_based_upon_size(profile, available_nodes):
    """
    Persist the list of large BSC nodes and filter nodes to only return the large node if required.

    :param profile: Profile object requesting the nodes
    :type profile: `Profile`
    :param available_nodes: List of ENM node objects
    :type available_nodes: list

    :return: List of ENM node objects
    :rtype: list
    """
    cell_key = None
    exclude = None
    # If the profile is going to call the batch mo function, it should reduce the node count then
    max_nodes = (None if hasattr(profile, 'BATCH_MO_SIZE')
                 else profile.MAX_NODES_TO_ALLOCATE if hasattr(profile, 'MAX_NODES_TO_ALLOCATE') else None)
    if hasattr(profile, "LARGE_BSC_ONLY"):
        cell_key = "LARGE_BSC"
        exclude = not profile.LARGE_BSC_ONLY
    elif hasattr(profile, "SMALL_BSC_ONLY"):
        cell_key = "SMALL_BSC"
    elif hasattr(profile, "BSC_250_CELL"):
        cell_key = "BSC_250_CELL"
    if cell_key:
        persist_dict_value("GSM_KEYS")
        available_nodes = update_available_nodes(available_nodes, cell_key, exclude=exclude)
        random.shuffle(available_nodes)
    return available_nodes if not max_nodes else available_nodes[:max_nodes]


def handle_one_total_node_and_multiple_support_types(profile, available_nodes):
    """
    If a profile has multiple supported types but only needs 1 total node, the profile will be over allocated nodes
    proportionally to the number of supported node types.
    :param profile: Profile object
    :type profile: enmutils_int.lib.profile.Profile
    :param available_nodes: list of available nodes
    :type available_nodes: list
    :return: List of nodes available nodes.
    :rtype: list
    """

    if (hasattr(profile, 'TOTAL_NODES') and hasattr(profile, 'SUPPORTED_NODE_TYPES') and
            profile.TOTAL_NODES == 1 and len(available_nodes) > profile.TOTAL_NODES):
        return available_nodes[:profile.TOTAL_NODES]
    return available_nodes


def update_available_nodes(available_nodes, cell_key, exclude=None):
    """
    Update the existing list of nodes if required

    :param available_nodes: List of ENM node objects
    :type available_nodes: list
    :param cell_key: Specific cell type to be used for selection of nodes
    :type cell_key: str
    :param exclude: Exclude the specific node objects
    :type exclude: bool

    :return: Updated list of ENM node objects
    :rtype: list
    """
    log.logger.debug("{1} nodes of type {0}".format(cell_key, "Excluding" if exclude else "Including"))
    nodes_to_validate_against = persistence.get(KEY_MAPPINGS.get(cell_key))
    if not nodes_to_validate_against:
        log.logger.debug("No nodes to validate against, re-attempting key persist.")
        persist_dict_value(cell_key)
        nodes_to_validate_against = persistence.get(KEY_MAPPINGS.get(cell_key))
        if not nodes_to_validate_against:
            log.logger.debug("Failed to determine nodes to base filtering upon, continuing with available nodes.")
            return available_nodes
    if exclude:
        available_nodes = [available_node for available_node in available_nodes if available_node.node_id
                           not in nodes_to_validate_against]
    else:
        available_nodes = [available_node for available_node in available_nodes if available_node.node_id in
                           nodes_to_validate_against]
    log.logger.debug("Filtering of nodes completed.")
    return available_nodes


def persist_dict_value(key, ttl=172800):
    """
    Set the dictionary in persistence if available, based upon the supplied key

    :param key: Identifier of the required key to be set in persistence
    :type key: str
    :param ttl: Time to live for the persisted object
    :type ttl: int
    """
    log.logger.debug("Starting key persist operation.")
    if key:
        all_keys = persistence.get_all_keys()
        mo_dict = generate_cell_dict(key)
        if key == "EUTRANCELL" and (mo_dict.get("TDD") or mo_dict.get("FDD")):
            key, value = EUTRANCELL_NODE_DICT, mo_dict
            global LTE_DICT
            LTE_DICT = mo_dict
            persistence.set(key, value, ttl)
        elif key == "GSM_KEYS":
            for _ in ["SMALL_BSC", "LARGE_BSC", "BSC_250_CELL"]:
                key, value = KEY_MAPPINGS.get(_), mo_dict.get(_)
                if key not in all_keys and value:
                    persistence.set(key, value, ttl)
    else:
        log.logger.debug("No key value supplied, nothing to do.")


def get_synced_nodes(ne_type=None, node_ids=None):
    """
    Query ENM for a list of synchronised node ids

    :param ne_type: Filter by an ENM supported ne type
    :type ne_type: str
    :param node_ids: list of nodes separated by semicolon in string format
    :type node_ids: str
    :return: List of synchronised node id
    :rtype: list
    """
    log.logger.debug("Checking sync status of nodes.")
    synced_nodes = []
    node_ids = node_ids if node_ids else "*"
    cmd_stub = 'cmedit get {0} CmFunction.SyncStatus==SYNCHRONIZED'.format(node_ids)
    cmd = '{1} -ne={0}'.format(ne_type, cmd_stub) if ne_type else cmd_stub
    user = get_workload_admin_user()
    try:
        response = user.enm_execute(cmd)
        output = response.get_output()
        if output:
            synced_nodes = [line.split("Element=")[1].split(",")[0].encode('utf-8') for line in output if "FDN" in line]
        log.logger.debug("Sync status check completed.")
        return synced_nodes
    except Exception as e:
        log.logger.debug("Failed to retrieve list of synced nodes from ENM, response: {0}".format(str(e)))
        return synced_nodes


def filter_unsynchronised_nodes(nodes, ne_type=None):
    """
    Filter out any unsynchronised nodes allocated to the profile

    :param nodes: List nodes allocated to the profile
    :type nodes: list
    :param ne_type: Filter by an ENM supported ne type
    :type ne_type: str

    :return: List of filtered synchronised nodes allocated to the profile
    :rtype: list
    """
    node_ids = ";".join([node.node_id for node in nodes])
    list_of_synced_node_ids = get_synced_nodes(ne_type=ne_type, node_ids=node_ids)
    synced = [node for node in nodes if node.node_id in list_of_synced_node_ids]
    log.logger.debug("Found a total of {0} synchronised nodes.".format(len(synced)))
    log.logger.debug("Node(s) selected for operations: {0}".format(', '.join(str(node_id) for node_id in synced)))
    return synced


def match_cardinality_requirements(profile, available_nodes, node_type):
    """
    Select nodes matching the cardinality requirements

    :param profile: Profile object requesting the nodes
    :type profile: `Profile`
    :param available_nodes: List of ENM node objects
    :type available_nodes: list
    :param node_type: Node type to apply the cardinality check to
    :type node_type: str

    :return: List of ENM node objects
    :rtype: list
    """
    log.logger.debug("Determining if cardinality check required for profile.")
    skip_ne_type = (bool(node_type not in getattr(profile, 'CELL_CARDINALITY_NES')) if
                    hasattr(profile, 'CELL_CARDINALITY_NES') else False)
    if (not hasattr(profile, "CELL_CARDINALITY") or not hasattr(profile.CELL_CARDINALITY, "__getitem__") or
            skip_ne_type or not available_nodes):
        log.logger.debug('Profile does not require cardinality check.')
        return available_nodes
    log.logger.debug("Starting cardinality check.")
    try:
        nss_mo = nss_mo_info.NssMoInfo(group_nodes_per_netsim_host(get_pool().nodes))
        nss_mo.fetch_and_parse_netsim_simulation_files()
    except Exception as e:
        log.logger.debug("Failed to generate one or more files, error encountered: {0}".format(str(e)))
    all_matched_nodes, previously_matched_nodes = [], []
    for mo_name, cardinality in profile.CELL_CARDINALITY.iteritems():
        if getattr(cardinality, '__getitem__', None):
            cardinality = list(cardinality)
            min_cardinality, max_cardinality = cardinality[0], cardinality[-1]
        else:
            min_cardinality, max_cardinality = int(cardinality), None

        mo_selection = node_mo_selection.NodeMoSelection()
        current_matched_nodes = mo_selection.select_all_with_required_mo_cardinality(mo_name,
                                                                                     min_cardinality=min_cardinality,
                                                                                     max_cardinality=max_cardinality,
                                                                                     nodes=available_nodes)
        if not current_matched_nodes:
            return []
        if not previously_matched_nodes:
            previously_matched_nodes = current_matched_nodes
        all_matched_nodes = set(previously_matched_nodes).intersection(current_matched_nodes)
    log.logger.debug("Completed cardinality check.")
    return list(all_matched_nodes)


def get_all_nodes_from_redis(ignore_keys):
    """
    Retrieve all instance(s) of load_node.LoadNodeMixin from persistence

    :param ignore_keys: List of keys to ignore
    :type ignore_keys: List

    :return: List of all instance(s) of load_node.LoadNodeMixin from persistence
    :rtype: list
    """
    start_time = datetime.datetime.now()
    process.get_current_rss_memory_for_current_process()
    log.logger.debug("Starting fetch of all nodes from redis")

    excluded_patterns = ['mutex', 'workload', 'command-executor', 'session',
                         'count', 'status', 'errors', 'warnings', 'ddp_host',
                         '-mos', '-nodes', 'assertion', 'PLM_FILES_IMPORTED', 'ALLOCATED',
                         EUTRANCELL_NODE_DICT, LARGE_BSC, SMALL_BSC, BSC_250_CELL,
                         PROFILE_NOTIFICATION_VALUES, PROFILE_NODE_ALLOCATION_VALUES]

    all_keys = list(set(persistence.get_all_default_keys()).difference(ignore_keys))
    keys = [key for key in all_keys if not any(pattern in key for pattern in excluded_patterns)]

    log.logger.debug("Filtering out active profiles from keys to be fetched")
    active_profiles = persistence.get("active_workload_profiles") or set()
    for profile in active_profiles:
        for key in keys[:]:
            if profile in key:
                keys.remove(key)

    persisted_nodes = []
    if keys:
        log.logger.debug("Fetching objects from redis for {0} keys".format(len(keys)))
        persisted_nodes = [node for node in persistence.get_key_values_from_default_db(keys)
                           if isinstance(node, enm_node.BaseNode)]

        elapsed_time = datetime.datetime.now()
        process.get_current_rss_memory_for_current_process()
        log.logger.debug("Completed fetch of all {0} node(s) from redis. Total time taken {1} second(s)."
                         .format(len(persisted_nodes), (elapsed_time - start_time).total_seconds()))
    else:
        log.logger.debug("No nodes found")
    return persisted_nodes


def get_node_oss_prefixes(nodes):
    """
    Query ENM for the supplied list of node ids, OSSPrefix values

    :param nodes: List of node ids created in ENM
    :type nodes: list

    :raises EnmApplicationError: raised if the ENM command is not successful

    :return: Dictionary containing the ENM ossPrefix value for the supplied node ids
    :rtype: dict
    """
    node_oss_prefixes = {}
    user = get_workload_admin_user()
    cmd = "cmedit get {node_ids} NetworkElement.ossPrefix".format(node_ids=";".join(nodes))
    try:
        response = user.enm_execute(cmd)
        for index, line in enumerate(response.get_output()):
            if "FDN" in line:
                oss_prefix = response.get_output()[index + 1].split(":")[-1].strip() if "ossPrefix" in response.get_output()[index + 1] else ""
                node_oss_prefixes[line.split("NetworkElement=")[-1].strip()] = oss_prefix
        return node_oss_prefixes
    except Exception as e:
        log.logger.debug("Could not retrieve ENM OSS prefix value, error encountered: {0}.".format(str(e)))
        raise EnmApplicationError(str(e))


def get_unique_nodes(node_dict, node_type):
    """
    Get list of unique nodes from node dict catering for older node types too

    :param node_dict: Node dictionary, where each key is a different node type
    :type node_dict: dict
    :param node_type: Node type
    :type node_type: str
    :return: List of node objects
    :rtype: list
    """
    nodes = []
    if node_type in node_dict.keys():
        default_nodes = node_dict[node_type].values()
        default_node_ids = node_dict[node_type].keys()
        nodes.extend(default_nodes)

        if node_type in UPDATED_NODES.keys():
            old_node_type = UPDATED_NODES.get(node_type)
            old_nodes_ids = node_dict[old_node_type].keys()

            for node_id in old_nodes_ids:
                if node_id not in default_node_ids:
                    nodes.append(node_dict[old_node_type][node_id])

    return nodes


def create_lite_nodes_using_attribute_filter(nodes, node_attributes=None):
    """
    Get list of lite node objects which have attributes

    :param nodes: List of node objects
    :type nodes: list
    :param node_attributes: List of node attributes to be included
    :type node_attributes: list
    :return: List of BasicNodeLite objects
    :rtype: list
    """
    default_node_attributes = ['node_id']
    node_attributes = node_attributes if node_attributes else default_node_attributes

    log.logger.debug("Extracting following node attributes: {0}".format(node_attributes))
    lite_nodes = []
    for node in nodes:
        node_attributes = node_attributes if "all" not in node_attributes else node.to_dict().keys()
        new_node_dict = {key: getattr(node, key) for key in node_attributes}
        lite_nodes.append(enm_node.BaseNodeLite(**new_node_dict))

    log.logger.debug("Fetching {0} node(s) complete".format(len(lite_nodes)))
    return lite_nodes


def get_all_nodes_with_predefined_attributes(profile, node_attributes=None):
    """
    Get list of node objects which have certain set of predefined attributes
    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile'
    :param node_attributes: List of node attributes to be included
    :type node_attributes: list
    :return: List of BasicNodeLite objects
    :rtype: list
    """
    log.logger.debug("Get all nodes in pool")
    node_dict = get_pool().node_dict
    nodes = sorted(list(set([node for node_type in node_dict for node in node_dict[node_type].values()])))
    log.logger.debug("Number of nodes found in pool: {0}".format(len(nodes)))

    if hasattr(profile, "NUM_NODES"):
        nodes = []
        log.logger.debug("Filtering nodes by type in NUM_NODES: {0}".format(profile.NUM_NODES))
        for node_type in profile.NUM_NODES.keys():
            nodes.extend(get_unique_nodes(node_dict, node_type))
        log.logger.debug("Number of nodes after filtering: {0}".format(len(nodes)))

    return create_lite_nodes_using_attribute_filter(nodes, node_attributes=node_attributes)


def get_all_nodes_using_separate_process(profile, node_attributes=None):
    """
    Get list of node objects, by running function in separate process (to reduce memory consumption)

    :param profile: Profile object using the saved search
    :type profile: `enmutils_int.lib.profile.Profile`
    :param node_attributes: List of node attributes to be included
    :type node_attributes: list
    :return: List of BasicNodeLite objects
    :rtype: list
    """
    return multitasking.create_single_process_and_execute_task(get_all_nodes_with_predefined_attributes,
                                                               args=(profile, node_attributes), fetch_result=True)


def get_allocated_nodes_with_predefined_attributes(profile_name, node_attributes=None):
    """
    Get list of node objects which have certain set of predefined attributes
    :param profile_name: Name of profile
    :type profile_name: str
    :param node_attributes: List of node attributes to be included
    :type node_attributes: list
    :return: List of BasicNodeLite objects
    :rtype: list
    """
    log.logger.debug("Fetching nodes allocated to {0}".format(profile_name))
    nodes = get_pool().allocated_nodes(profile_name)

    return create_lite_nodes_using_attribute_filter(nodes, node_attributes=node_attributes)


def get_allocated_nodes(profile_name, node_attributes=None):
    """
    Get list of node objects, by running function in separate process (to reduce memory consumption)

    :param profile_name: Name of profile
    :type profile_name: str
    :param node_attributes: List of node attributes to be included
    :type node_attributes: list
    :return: List of BasicNodeLite objects
    :rtype: list
    """
    return multitasking.create_single_process_and_execute_task(get_allocated_nodes_with_predefined_attributes,
                                                               args=(profile_name, node_attributes), fetch_result=True)


def exchange_nodes_allocated_to_profile(profile_name):
    """
    Exchange nodes allocated to profile

    :param profile_name: Name of Profile
    :type profile_name: str
    """
    profile = persistence.get(profile_name)
    try:
        deallocate_nodes(profile=profile)
        allocate_nodes(profile=profile)
    except Exception as e:
        profile.add_error_as_exception(e)


def update_lte_node(node):
    """
    Update the Cell type attribute on LTE nodes

    :param node: Load node instance to be checked and updated
    :type node: `load_node.LoadNodeMixin`

    :return: Updated Load node instance
    :rtype: `load_node.LoadNodeMixin`
    """
    if node.primary_type in ["ERBS", "RadioNode"] and not node.lte_cell_type:
        global LTE_DICT
        if not LTE_DICT:
            cell_dict = persistence.get(EUTRANCELL_NODE_DICT)
            if cell_dict:
                LTE_DICT = cell_dict
            else:
                persist_dict_value("EUTRANCELL")
        # Dictionary will be empty if the network is not synchronised
        for key, values in LTE_DICT.items():
            if key in ["FDD", "TDD"] and node.node_id in values:
                setattr(node, 'lte_cell_type', key)
    return node


def group_nodes_per_me_type(nodes):
    """
    Groups the given nodes based on the managed element type.
    :type nodes: list
    :param nodes: list of nodes
    :rtype: dict
    :return: dict of managed_element_type, and their corresponding nodes
    """
    nodes_with_me_types = {}
    for node in nodes:
        if node.managed_element_type not in nodes_with_me_types:
            nodes_with_me_types[node.managed_element_type] = []
        nodes_with_me_types.get(node.managed_element_type).append(node)

    return nodes_with_me_types


def group_nodes_per_ne_type(nodes):
    """
    Groups the given nodes based on the network element type.
    :type nodes: list
    :param nodes: list of nodes
    :rtype: dict
    :return: dict of primary_type (node type), and their corresponding nodes
    """
    nodes_with_ne_types = {}
    for node in nodes:
        if node.primary_type not in nodes_with_ne_types:
            nodes_with_ne_types[node.primary_type] = []
        nodes_with_ne_types.get(node.primary_type).append(node)

    return nodes_with_ne_types
