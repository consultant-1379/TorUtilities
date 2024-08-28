import json
import random
import re
import time

from functools import partial
from requests.exceptions import ConnectionError, HTTPError
from retrying import retry
from enmutils.lib import persistence
from enmutils.lib.persistence import picklable_boundmethod


from enmutils.lib import arguments, log
from enmutils.lib.exceptions import (EnmApplicationError, EnvironError, ProfileWarning,
                                     ScriptEngineResponseValidationError)
from enmutils_int.lib import netex
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.em import get_poids
from enmutils_int.lib.netex import (Collection, Search, get_all_collections,
                                    search_collections, download_exported_collections, create_export_dir_and_file,
                                    initiate_import_collections, retrieve_import_collection_status)
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

DELETE_COLLECTIONS_CHUNK_SIZE = 50


class NetexCollectionFlow(GenericFlow):
    """
    Common parent for profile flows using collections
    """
    def __init__(self):
        """
        Initialize the flow.
        """
        super(NetexCollectionFlow, self).__init__()

    def cleanup_collections(self, user, cleanup_collection, collection_ids):
        """
        Clean up leaf collections created by the profiles in current or past iterations.

        :param user: List of users handling the collection in ENM
        :type user: list
        :param cleanup_collection: collection object used to clean up
        :type cleanup_collection: `netex.Collection`
        :param collection_ids: list of collction ids to be deleted
        :type collection_ids: list
        :return: True if cleanup is successful completely False otherwise.
        :rtype: bool
        """
        cleanup_success = False
        log.logger.debug("Attempting to delete given collections.")
        failed_collection_ids = []
        log.logger.debug("Number of collections to be cleaned up - {0}".format(len(collection_ids)))
        for collection_ids_chunk in chunks(collection_ids, DELETE_COLLECTIONS_CHUNK_SIZE):
            chunk_delete_response = cleanup_collection.delete(collection_ids_chunk)
            if chunk_delete_response.status_code == 200:
                failed_collection_ids.extend([collection["id"] for collection in chunk_delete_response.json()
                                              if "id" in collection])
                log.logger.debug("Failed collection chunk delete response "
                                 "- {0}".format(chunk_delete_response.json()))
        teardown_collections = [collection_obj for collection_obj in self.teardown_list
                                if isinstance(collection_obj, Collection)]
        for collection_id in collection_ids:
            if collection_id not in failed_collection_ids:
                collection_in_teardown = [collection for collection in teardown_collections
                                          if collection.id == collection_id]
                if collection_in_teardown and collection_in_teardown[0] in self.teardown_list:
                    self.teardown_list.remove(collection_in_teardown[0])
        if failed_collection_ids:
            log.logger.debug("Failed to delete {0} leaf collection(s). "
                             "Please check ENM GUI/log viewer for "
                             "more information.".format(len(failed_collection_ids)))
        else:
            cleanup_success = True
            log.logger.debug("Successfully deleted all given collections.")
        return cleanup_success

    def cleanup_collections_based_on_type(self, user, collection_type="LEAF", custom_topology=False):
        """
        Attempt to clean up collections given the type such as LEAF, BRANCH or CUSTOM_TOPOLOGY.

        :param user: User handling the collection in ENM.
        :type user: `enm_user_2.User`
        :param collection_type: LEAF, BRANCH or CUSTOM_TOPOLOGY.
        :type collection_type: str
        :param custom_topology: Indicate whether the branch is a custom topology.
        :type custom_topology: bool
        :return: True if cleanup is successful completely False otherwise.
        :rtype: bool
        """
        log.logger.debug("Attempting to clean up any {0} collections created by the profile.".format(collection_type.lower()))
        cleanup_success = False
        try:
            cleanup_collection = Collection(user=user, name="{0}_for_cleanup".format(self.identifier))
            if collection_type == "BRANCH" and not custom_topology:
                payload = {"clauses": [{"type": collection_type, "negate": False}, {"type": "CUSTOM_TOPOLOGY", "negate": True}]}
            else:
                payload = {"clauses": [{"type": collection_type, "negate": False}]}
            response = search_collections(user, payload)
            collection_ids = [collection["id"] for collection in response.json() if self.NAME.lower() in collection["name"]]
            cleanup_success = self.cleanup_collections(user, cleanup_collection, collection_ids)
            log.logger.debug("Completed attempt to clean up any {0} collections created by the profile.".format(collection_type.lower()))
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        return cleanup_success

    def cleanup_leaf_branch_topology(self, user):
        """
        Attempt to clean up leaf, branch and topology collections if they are on one level each.

        :param user: User handling the collection in ENM
        :type user: `enm_user_2.User`
        """
        cleanup_leaf = self.cleanup_collections_based_on_type(user, collection_type="LEAF")
        if cleanup_leaf:
            cleanup_branch = self.cleanup_collections_based_on_type(user, collection_type="BRANCH")
            if cleanup_branch:
                self.cleanup_collections_based_on_type(user, collection_type="CUSTOM_TOPOLOGY")

    def delete_collections(self, collections, user):
        """
        Functionality to handle deletion and removal from teardown list of Collection objects.

        :param collections: List of `netex.Collection` objects to create
        :type collections: list
        :param user: User handling the collection in ENM
        :type user: `enm_user_2.User`
        """
        try:
            if collections:
                log.logger.debug("Attempting to clean up any leaf collections "
                                 "created by the profile in the current run.")
                cleanup_collection = collections[0]
                collection_ids = [collection.id for collection in collections]
                self.cleanup_collections(user, cleanup_collection, collection_ids)
                log.logger.debug("Attempt completed to clean up any leaf collections "
                                 "created by the profile in the current run.")
            else:
                log.logger.debug("No leaf collections available for the clean up of the current run.")
        except Exception as e:
            self.add_error_as_exception(e)

    def cleanup_teardown(self):
        """
        Clean up teardown at the end of the iteration.
        """
        log.logger.debug("Attempting to clean up collection or search objects in "
                         "teardown at the end of the iteration.")
        for teardown_object in self.teardown_list[::-1]:
            if isinstance(teardown_object, (Collection, Search)):
                self.teardown_list.remove(teardown_object)
        log.logger.debug("Completed attempt to clean up collection or search objects in "
                         " teardown at the end of the iteration.")

    def get_poids_from_search(self, user):
        """
        Retrieve ids from search query for creating the collection

        :param user: User handling the collection in ENM
        :type user: `enm_user_2.User`
        :return: po ids returned from the search
        :rtype: list
        """
        po_ids = None
        log.logger.debug("Attempting to retrieve po ids from search query for creating the collection.")
        try:
            search = Search(user, self.COLLECTION_QUERY, version="v2")
            search_response = search.execute()
            po_ids = [_["id"] for _ in search_response["objects"]]
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        else:
            log.logger.debug("Completed attempt to retrieve po ids from search query for creating the collection.")
        return po_ids


class Netex01Flow(NetexCollectionFlow):
    """
    Profile flow for NETEX_01
    """

    QUERY_TO_USERS = [
        ["select all objects of type RfBranch with attr auPortRef, dlAttenuation, "
         "dlAttenuationPerFqRange, dlTrafficDelay, dlTrafficDelayPerFqRange, "
         "reservedBy, rfBranchId, userLabel, rfPortRef, tmaRef", 40, 11],
        ["AntennaNearUnit where attr administrativeState = UNLOCKED", 3, 1],
        ["RfBranch", 2, 1],
        ["RfBranch where RfBranch has attr rfBranchId = 1 or attr rfBranchId = 2", 4, 1],
        ["{partial_node_regex}*", 19, 6],
        ["MeContext where MeContext has parent SubNetwork and SubNetwork has attr SubNetworkId=NETSimW", 4, 1],
        ["PlmnId where PlmnId has parent MeContext", 4, 1],
        ["select all objects of type RfBranch with attr auPortRef, dlAttenuation, "
         "dlAttenuationPerFqRange, dlTrafficDelay, dlTrafficDelayPerFqRange, "
         "reservedBy, rfBranchId, userLabel, rfPortRef, tmaRef from node type RadioNode", 4, 1],
        ["select all nodes of type RadioNode", 5, 1],
        ["{saved_search_name}", 2, 1],
        ["RfBranch from search {saved_search_name} where rfBranchId=1", 5, 1],
        ["MeContext from collection {large_collection_name}", 1, 1],
        ["MeContext from collection {small_collection_name}", 1, 1],
        ["MeContext and RfBranch using collection {small_collection_name}", 2, 1],
        ["RfBranch using collection {small_collection_name}", 1, 1],
        ["{small_collection_name}", 2, 1]
    ]

    COLLECTION_QUERY = "select all nodes of type RadioNode"
    SEARCH_QUERY = "select RfBranch"

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        SEARCH_NAME = "{0}_saved_search_rfbranch".format(self.NAME)
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        self.assign_users_to_queries(users)
        setup_user = users[0]
        self.cleanup_collections_based_on_type(setup_user, collection_type="LEAF")
        self.state = "RUNNING"
        while self.keep_running():
            large_collection_name = "{0}_Large_RadioNode_Collection_{1}".format(self.NAME,
                                                                                arguments.get_random_string(size=6))
            small_collection_name = "{0}_Small_RadioNode_Collection_{1}".format(self.NAME,
                                                                                arguments.get_random_string(size=6))
            large_collection, teardown_large_collection = netex.search_and_create_collection(self, setup_user,
                                                                                             self.COLLECTION_QUERY,
                                                                                             large_collection_name, [],
                                                                                             num_results=self.NUM_RESULTS_LARGE_COLLECTION,
                                                                                             delete_existing=True)
            small_collection, teardown_small_collection = netex.search_and_create_collection(self, setup_user,
                                                                                             self.COLLECTION_QUERY,
                                                                                             small_collection_name, [],
                                                                                             num_results=500,
                                                                                             delete_existing=True)
            search, teardown_search = netex.search_and_save(self, setup_user, self.SEARCH_QUERY, SEARCH_NAME,
                                                            nodes=None, delete_existing=True, version="v2")
            log.logger.debug("Sleeping for 30 seconds to get the saved search and collections updated in the database.")
            time.sleep(30)
            try:
                self.execute_netex_query_flow(self, large_collection, small_collection, search)
            except Exception as e:
                self.add_error_as_exception(EnvironError(e))
            self._cleanup(teardown_large_collection, teardown_small_collection, teardown_search)
            self.cleanup_teardown()
            self.sleep()

    def _cleanup(self, *args):
        """
        Method to delete collection and search object(s) after each iteration

        :param args: list of objects to be cleaned up
        :type args: list
        """
        for arg in args:
            try:
                if arg.id:
                    arg.delete()
                    if arg in self.teardown_list:
                        self.teardown_list.remove(arg)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))

    def assign_users_to_queries(self, users):
        """
        Add a list containing the required number of users to each matching query key

        :param users: List of profiles users to be assigned
        :type users: `enm_user_2.User`
        """
        i = 0
        num_user_index = 1 if self.NUM_USERS == 99 else 2
        for query in self.QUERY_TO_USERS:
            num_user_req = query[num_user_index]
            query.append(users[i: i + num_user_req])
            i += num_user_req

    @staticmethod
    def execute_netex_query_flow(profile, large_collection, small_collection, search):
        """
        Builds and executes the Netex Flow objects

        :param profile: Profile that is invoking the flow
        :type profile: `profile.Netex01Flow`
        :param large_collection: Large Collection object used as part of the query
        :type large_collection: `netex.Collection`
        :param small_collection: Small Collection object used as part of the query
        :type small_collection: `netex.Collection`
        :param search: Search object used as part of the query
        :type search: `netex.Search`
        """
        flow_list = []

        for query in profile.QUERY_TO_USERS:
            for user in query[3]:
                flow_list.append(netex.NetexFlow(profile, user, query[0],
                                                 large_collection=large_collection,
                                                 small_collection=small_collection,
                                                 saved_search=search,
                                                 version="v2"))
        random.shuffle(flow_list)
        if flow_list:
            flow_list[0]._navigate_netex_app_help()
        for flow in flow_list:
            flow.execute_flow()


class Netex02Flow(NetexCollectionFlow):
    """
    Profile flow for NETEX_02
    """
    QUERY = "select MeContext"

    def create_collection(self, collection_list, user):
        """
        Functionality to handle creation and clean up of Collection objects

        :param collection_list: List of `netex.Collection` objects to create
        :type collection_list: list
        :param user: User who will create the collection in ENM
        :type user: `enm_user_2.User`

        :return: List of created `netex.Collection` instances
        :rtype: list
        """
        for collection in collection_list[:]:
            try:
                collection.create()
            except Exception as e:
                collection_list.remove(collection)
                self.add_error_as_exception(e)
            else:
                self.teardown_list.append(collection)
        time.sleep(5)
        if len(collection_list) < self.NUM_COLLECTIONS:
            self.add_error_as_exception(EnmApplicationError("Number of collections created ({0}) is less than "
                                                            "collections required ({1})"
                                                            .format(len(collection_list), self.NUM_COLLECTIONS)))
        return collection_list

    def update_collection(self, collection, nodes):
        """
        Gets the PO IDs for additional nodes to be added to collection
        and updates the collection with them.

        :param collection: `netex.Collection` objects to create
        :type collection: `netex.Collection`
        :param nodes: List of nodes to be added to collection
        :type nodes: list
        """
        additional_nodes = random.sample(list(set(nodes) - set(collection.nodes)),
                                         self.ADDITIONAL_NODES_PER_COLLECTION)
        collection.nodes = collection.nodes + additional_nodes
        node_poids = get_poids(collection.nodes)[0]
        collection.update_collection(node_poids=node_poids)

    def create_collection_objects(self, nodes, users):
        """
        Create the list of collection objects allocating from the available nodes

        :param nodes: List of `enm_node.Node` instances
        :type nodes: list
        :param users: List of `enm_user_2.User` instances
        :type users: list

        :return: List of `netex.Collection` instances
        :rtype: list
        """
        collections = []
        log.logger.debug("Gathering nodes for {0} collections. {1} collections with {2} available nodes "
                         "in each.".format(self.NAME, self.NUM_COLLECTIONS, len(nodes)))
        for i in xrange(self.NUM_COLLECTIONS):
            try:
                user = users[i] if self.NAME == "NETEX_02" else users[0]
                new_nodes = random.sample(nodes, self.NODES_PER_COLLECTION)
                collections.append(Collection(user=user, name="{0}-COLLECTION-{1}".format(self.identifier, i),
                                              nodes=new_nodes))
            except ValueError:
                self.add_error_as_exception(
                    EnmApplicationError("Number of nodes - {0} is less than "
                                        "number of nodes per collection - {1}".format(len(nodes),
                                                                                      self.NODES_PER_COLLECTION)))
            except IndexError:
                self.add_error_as_exception(EnmApplicationError("Required number of Users are not created"))
        return collections

    def collection_flow(self, users, nodes):
        """
        Flow to create, update, get and delete collections

        :param users: List of `enm_user_2.User` instances
        :type users: list
        :param nodes: List of `enm_node.Node` instances
        :type nodes: list
        """
        log.logger.info("Executing flow for collections as the iteration is even")
        collections = self.create_collection_objects(nodes, users)
        created_collections = self.create_collection(collections, users[0])
        log.logger.debug("Sleeping for 60 seconds before running UPDATE and GET cycle.")
        time.sleep(60)
        for collection in collections[:]:
            try:
                self.update_collection(collection, nodes)
                collection.get_collection_by_id(collection_id=collection.id,
                                                include_contents=True)
                get_all_collections(collection.user)
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.debug("Sleeping for 60 seconds before running DELETE cycle.")
        time.sleep(60)
        self.delete_collections(created_collections, users[0])

    def saved_search_flow(self, users):
        """
        Flow to create, get and delete saved searches

        :param users: List of `enm_user_2.User` instances
        :type users: list
        """
        log.logger.info("Executing flow for saved searches as the iteration is odd")
        for user in users:
            try:
                search = Search(name=user.username, user=user, query=self.QUERY, version="v2")
                # Delete saved search if it already exists and then proceed with the flow
                if search.exists:
                    search.delete()
                search.save()
                self.teardown_list.append(search)
                search.get_saved_search_by_id()
                search._get_saved_searches()
                search.delete()
                self.teardown_list.remove(search)
            except Exception as e:
                self.add_error_as_exception(e)

    def execute_flow(self):
        """
        Executes the profile flow
        """
        users = self.create_profile_users(self.NUM_COLLECTIONS, self.USER_ROLES)
        self.cleanup_collections_based_on_type(users[0], collection_type="LEAF")
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid"])
        odd_iteration = False
        self.state = "RUNNING"
        while self.keep_running():
            if odd_iteration:
                self.saved_search_flow(users)
            else:
                self.collection_flow(users, nodes)
            self.cleanup_teardown()
            # Flip the value between False and True
            odd_iteration ^= True
            self.sleep()


class Netex03Flow(GenericFlow):
    """
    Profile flow for NETEX_03
    """

    QUERY = "select EUtranCellFDD  where EUtranCellFDD has attr administrativeState = LOCKED from node type RadioNode"
    CMD_NUM_LOCKED_CELLS = "cmedit get * EUtranCellFDD.administrativeState==LOCKED -netype=RadioNode -cn"
    CMD_GET_LOCKED_CELLS = "cmedit get * EUtranCellFDD.administrativeState==LOCKED -netype=RadioNode"
    CMD_GET_UNLOCKED_CELLS = "cmedit get * EUtranCellFDD.administrativeState==UNLOCKED -netype=RadioNode"
    CMD_TO_UNLOCK_CELLS = "cmedit set {} EUtranCellFDD.administrativeState=UNLOCKED"
    CMD_TO_LOCK_CELLS = "cmedit set {} EUtranCellFDD.administrativeState=LOCKED"
    EXTRACT_INSTANCES_VALUE = r"\d+(?=\sinstance\(s\))"
    num_locked_cells = 0
    user = None

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        self.state = "RUNNING"
        self.teardown_list.append(partial(picklable_boundmethod(self.remove_persistence_value)))
        while self.keep_running():
            self.sleep_until_time()
            num_exceptions = self.adjust_num_cells()
            time.sleep(10)
            search = Search(user=self.user, query=self.QUERY, version="v2")
            self.execute_timed_query(search, num_exceptions)
            time.sleep(60)

    def adjust_num_cells(self):
        """
        Ensure expected number of cells are locked.
        Add/remove locked cells to match the number if required.
        :return: Number of exceptions if any
        :rtype: int
        """
        num_exceptions = 0
        self.num_locked_cells = self.get_number_of_locked_cells()
        log.logger.info("Number of locked cells - {0} and the expected number - {1}."
                        .format(self.num_locked_cells, self.EXPECTED_NUM_LOCKED_CELLS))
        if self.num_locked_cells > self.EXPECTED_NUM_LOCKED_CELLS:
            num_cells = self.num_locked_cells - self.EXPECTED_NUM_LOCKED_CELLS
            num_exceptions = self.match_cells(lock_type="unlock", num_cells=num_cells, get_cmd=self.CMD_GET_LOCKED_CELLS,
                                              execute_cmd=self.CMD_TO_UNLOCK_CELLS)
        elif self.num_locked_cells < self.EXPECTED_NUM_LOCKED_CELLS:
            num_cells = self.EXPECTED_NUM_LOCKED_CELLS - self.num_locked_cells
            num_exceptions = self.match_cells(lock_type="lock", num_cells=num_cells, get_cmd=self.CMD_GET_UNLOCKED_CELLS,
                                              execute_cmd=self.CMD_TO_LOCK_CELLS)
        return num_exceptions

    def match_cells(self, lock_type, num_cells, get_cmd, execute_cmd):
        """
        Change lock state of cells to match the expected number.
        :param lock_type: Action to be performed on the cells i.e lock/unlock
        :type lock_type: str
        :param num_cells: Number of cells to be locked/unlocked
        :type num_cells: int
        :param get_cmd: Command to get the number of locked/unlocked cells
        :type get_cmd: str
        :param execute_cmd: Command to change the administrative state of a cell to
                            locked/unlocked.
        :type execute_cmd: str
        :return: Number of exceptions if any
        :rtype: int
        """
        num_exceptions = 0
        log.logger.info("{0} {1} cells "
                        "to match the expected number.".format(lock_type, num_cells))
        response = ""
        try:
            response = self.user.enm_execute(get_cmd)
            output = response.get_output()
            fdns = [_.split("FDN : ")[1] for _ in output if "FDN : " in _]
        except Exception as e:
            self.add_error_as_exception(e)

        if not response:
            self.add_error_as_exception(
                ScriptEngineResponseValidationError(
                    "Response is not in the expected format "
                    "to get the cells information", response))
        else:
            for _ in range(0, num_cells):
                try:
                    self.user.enm_execute(execute_cmd.format(fdns[_]))
                except IndexError:
                    num_exceptions += 1
                except Exception as e:
                    self.add_error_as_exception(e)
        return num_exceptions

    def get_number_of_locked_cells(self):
        """
        Get the number of locked cells
        """
        instances_returned = 0
        try:
            num_locked_response = self.user.enm_execute(self.CMD_NUM_LOCKED_CELLS)
            num_locked_output = num_locked_response.get_output()
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            if "instance(s)" not in num_locked_output[-1]:
                self.add_error_as_exception(
                    ScriptEngineResponseValidationError("Response is not in the expected format "
                                                        "to get the number of locked cells", num_locked_response))
            instances_match = re.search(self.EXTRACT_INSTANCES_VALUE, num_locked_output[-1])
            if instances_match:
                instances_returned = int(instances_match.group(0))
        return instances_returned

    def execute_timed_query(self, search, num_exceptions):
        """
        Executes a search query, timing the execution time and volume of MOs returned

        :type search: `netex.Search`
        :param search: Search object to execute the query
        :param num_exceptions: Count of exceptions if any
        :type num_exceptions: int
        """
        # Time against which KTT asserts on
        required_time = self.NETEX_KTT_TIME_LIMIT
        start = time.time()
        try:
            response = search.execute(profile_name=self.NAME)
            if persistence.get("NETEX_03_re_establish"):
                start = persistence.get("NETEX_03_re_establish")
                self.teardown_list.append(persistence.get("NETEX_03_re_establish"))
            result_size = response["metadata"]["RESULT_SET_TOTAL_SIZE"]
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            end = time.time()
            elapsed_time = end - start
            success = bool(elapsed_time <= required_time)
            if not success:
                self.add_error_as_exception(EnmApplicationError("{0} response time {1} was outside the required {2} "
                                                                "seconds expected".format(self.NAME, elapsed_time,
                                                                                          required_time)))
            log.logger.debug("Query returned {0} LOCKED cells in {1} seconds.".format(result_size, elapsed_time))
            if result_size != self.EXPECTED_NUM_LOCKED_CELLS and num_exceptions:
                self.add_error_as_exception(EnvironError("There are not enough cells to lock/unlock in the deployment"))

    def remove_persistence_value(self):
        """
        This method is to remove the persistence value during teardown
        """
        persistence.remove("NETEX_03_re_establish")


class Netex04Flow(NetexCollectionFlow):
    """
    Profile flow for NETEX_04
    """

    def execute_flow(self):
        """
        Executes the Netex 04 flow
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        self.cleanup_collections_based_on_type(users[0], collection_type="LEAF")
        self.state = "RUNNING"
        while self.keep_running():
            log.logger.debug("Creating collection objects in each iteration to avoid "
                             "collection name conflicts."
                             "Also creating a single file of MOs for both create and update "
                             "collection from file scenarios in each iteration.")
            collections = []
            for i, user in enumerate(users):
                collection = Collection(user=user,
                                        name="{0}_collection_{1}_{2}".format(self.NAME,
                                                                             arguments.get_random_string(size=8), i),
                                        fdn_file_name="{0}_collection_file_{1}".format(self.NAME,
                                                                                       "create_or_update"))
                collections.append(collection)

            try:
                collections[0].create_file()
                log.logger.debug("Sleeping for 10 seconds after file is created.")
                time.sleep(10)
            except Exception as e:
                self.add_error_as_exception(e)
            else:
                self.create_and_execute_threads(collections, len(collections), args=[self])
            self.cleanup_teardown()
            self.sleep()

    def delete(self, collection):
        """
        Deletes a collection in netex

        :type collection: `netex.Collection`
        :param collection: an enm collection
        """
        try:
            collection.delete()
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            if collection in self.teardown_list:
                self.teardown_list.remove(collection)

    @staticmethod
    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError, ProfileWarning)),
           wait_fixed=30000, stop_max_attempt_number=3)
    def create_from_file(worker, profile):
        """
        Create collection from file and view it's contents.
        Retry if there is HTTPError or ConnectionError.

        :param worker: `enmutils_int.lib.netex.Collection`
        :type worker: Collection object to be created.
        :param profile:
        :type profile:
        :raises ProfileWarning: when a collection exists with the same name
                                as the one attempting to create.
        :raises HTTPError: when the HTTP response indicates an error.
        :raises ConnectionError: when there is a connection issue.
        """
        log.logger.debug("Attempting to create collection from file and view it's contents.")
        if not worker.exists:
            worker.create_collection_from_file()
            profile.teardown_list.append(worker)
            log.logger.debug("Sleeping for 10 seconds after collection is created from file.")
            time.sleep(10)
            worker.get_collection_by_id(collection_id=worker.id,
                                        include_contents=True)
            log.logger.debug("Successfully created collection from file and view it's contents.")
        else:
            raise ProfileWarning("A collection exists with the same name "
                                 "as the one attempting to create from file.")

    @staticmethod
    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError, ProfileWarning)),
           wait_fixed=30000, stop_max_attempt_number=3)
    def update_from_file(worker):
        """
        Update collection from file and view it's contents.
        Retry if there is HTTPError or ConnectionError.

        :param worker: `enmutils_int.lib.netex.Collection`
        :type worker: Collection object to be updated.
        :raises ProfileWarning: when collection to be updated was not created.
        :raises HTTPError: when the HTTP response indicates an error.
        :raises ConnectionError: when there is a connection issue.
        """
        log.logger.debug("Attempting to update collection from file and view it's contents.")
        if worker.exists:
            worker.update_collection_from_file(replace='true')
            log.logger.debug("Sleeping for 10 seconds after collection is updated from file.")
            time.sleep(10)
            worker.get_collection_by_id(collection_id=worker.id,
                                        include_contents=True)
            log.logger.debug("Successfully updated collection from file and view it's contents.")
        else:
            raise ProfileWarning("Collection to be updated from file was not created.")

    @staticmethod
    def task_set(worker, profile):
        """
        Performs a task on netex application via REST calls

        :type worker: `enmutils_int.lib.netex.Collection`
        :param worker: Collection object to be created [updated]
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """

        if worker.name.endswith("0"):
            try:
                profile.create_from_file(worker, profile)
            except Exception as e:
                profile.add_error_as_exception(e)
        else:
            try:
                worker.create()
                profile.teardown_list.append(worker)
                log.logger.debug("Sleeping for 10 seconds after empty collection is created, "
                                 "before updating it using file.")
                time.sleep(10)
                profile.update_from_file(worker)
            except Exception as e:
                profile.add_error_as_exception(e)
        profile.delete(worker)


class Netex05Flow(NetexCollectionFlow):
    """
    Profile flow for NETEX_05
    """
    COLLECTION_QUERY = "select all nodes"
    NUM_BRANCH_COLLECTIONS = 8
    NUM_LEAF_COLLECTIONS = 5
    NUM_ELEMENTS_IN_COLLECTION = 2000

    def execute_flow(self):
        """
        Executes the Netex 05 flow
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        sleep_time_before_cleanup = self.SLEEP_TIME_BEFORE_CLEANUP
        self.state = "RUNNING"
        while self.keep_running():
            self.cleanup_collections_based_on_type(users[0], collection_type="LEAF")
            self.create_and_traverse_topology_and_collections(users, sleep_time_before_cleanup)
            self.cleanup_teardown()
            self.sleep()

    def create_and_traverse_topology_and_collections(self, users, sleep_time_before_cleanup):
        """
        For each user,
            create required regular collections to be attached as leaf collections,
                            root custom topology,
                            branch collections,
                            leaf collections
            get root custom topology
            traverse the created collections
            clean up all the created objects

        :param users: list of ENM users
        :type users: list
        :param sleep_time_before_cleanup: Sleep time before cleaning up objects for the user
        :type sleep_time_before_cleanup: int
        """
        for user in users:
            log.logger.debug("Attempting to execute the required steps using user - {0}".format(user.username))
            root_custom_topology = self.create_root_custom_topology(user)
            if not root_custom_topology:
                self.add_error_as_exception(
                    EnmApplicationError("Root custom topology could not be created for {0}."
                                        "Will skip the flow for current user in this iteration.".format(user.username)))
                continue

            branch_collections, nested_collection_id = self.create_branch_collections(user,
                                                                                      root_custom_topology_id=root_custom_topology.id,
                                                                                      num_collections=self.NUM_BRANCH_COLLECTIONS)
            if not branch_collections or not nested_collection_id:
                self.add_error_as_exception(
                    EnmApplicationError("Branch collections could not be created for {0}."
                                        "Will skip the flow for current user in this iteration.".format(user.username)))
                continue
            poids = self.get_poids_from_search(user)
            leaf_collections = self.create_regular_collections_for_leaf(user,
                                                                        num_collections=self.NUM_LEAF_COLLECTIONS,
                                                                        level=self.NUM_BRANCH_COLLECTIONS + 1,
                                                                        parent_id=nested_collection_id,
                                                                        poids=poids)
            if not leaf_collections:
                self.add_error_as_exception(EnmApplicationError("Regular Collections to be used as leaf "
                                                                "could not be created for {0}."
                                                                "Will skip the flow for current user in "
                                                                "this iteration.".format(user.username)))
                continue

            try:
                root_custom_topology.get_collection_by_id(collection_id=root_custom_topology.id,
                                                          include_contents=True)
            except Exception:
                self.add_error_as_exception(
                    EnmApplicationError("Could not fetch root custom topology for {0}."
                                        "Will skip the flow for current user in this iteration.".format(user.username)))
                continue

            self.traverse_collections(user, root_custom_topology)
            log.logger.debug("Waiting for {0} seconds before the clean up.".format(sleep_time_before_cleanup))
            time.sleep(sleep_time_before_cleanup)
            self.cleanup(root_custom_topology, branch_collections, leaf_collections, user)
            log.logger.debug("Successfully executed the required steps using user - {0}".format(user.username))

    def create_regular_collections_for_leaf(self, user, num_collections=0, level=None, parent_id=None, poids=None):
        """
        Create required number of regular collections to be later used as leaf collections.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param num_collections: number of collections to be created
        :type num_collections: int
        :param level: level at which collection created exists
        :type level: str
        :param parent_id: parent collection id for the leaf collections to be created
        :type parent_id: str
        :param poids: po ids to be used to create collection
        :type poids: list
        :return: List of regular collections created
        :rtype: list
        """
        collections_for_leaf = []
        log.logger.debug("Attempting to create regular leaf collections required.")
        try:
            for i in range(1, num_collections + 1):
                collection_name = "level_{0}_leaf_{1}_{2}".format(level, i, self.identifier)
                collection_for_leaf = Collection(user=user, name=collection_name,
                                                 num_results=self.NUM_ELEMENTS_IN_COLLECTION,
                                                 parent_ids=[parent_id], poids=poids)
                collection_for_leaf.create()
                self.teardown_list.append(collection_for_leaf)
                collections_for_leaf.append(collection_for_leaf)
        except Exception as e:
            log.logger.debug("Regular collections to be used as leaf could not be created")
            self.add_error_as_exception(EnmApplicationError(e))
        else:
            log.logger.debug("Successfully created regular leaf collections required.")
        return collections_for_leaf

    def create_root_custom_topology(self, user):
        """
        Create root custom topology

        :param user: ENM user
        :type user: `enm_user_2.User`
        :return: Custom Topology object created
        :rtype: `netex.CustomTopology`
        """
        log.logger.debug("Attempting to create root custom topology.")
        try:
            root_custom_topology = Collection(user, name="custom_topology_{0}".format(self.identifier),
                                              type="BRANCH", custom_topology=True)
            self.teardown_list.append(root_custom_topology)
            root_custom_topology.create()
        except Exception:
            root_custom_topology = None
            self.add_error_as_exception(EnmApplicationError("Root custom topology could not be created"))
        else:
            log.logger.debug("Successfully created root custom topology.")
        return root_custom_topology

    def create_branch_collections(self, user, root_custom_topology_id, num_collections):
        """
        Create branch collections with the required number of levels.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param root_custom_topology_id: id of root custom topology
        :type root_custom_topology_id: str
        :param num_collections: number of collections to be created
        :type num_collections: int
        :return: Tuple containing list of branch collections created and id of the bottom most branch collection
        :rtype: tuple
        """
        branch_collections = []
        nested_collection_id = None
        log.logger.debug("Attempting to create branch collections.")
        try:
            for level in range(1, num_collections + 1):
                if level == 1:
                    nested_collection_id = root_custom_topology_id
                collection = Collection(user, name="level_{0}_branch_{1}".format(level, self.identifier),
                                        type="BRANCH", parent_ids=[nested_collection_id])
                branch_collections.append(collection)
                self.teardown_list.append(collection)
                collection.create()
                nested_collection_id = collection.id
        except Exception:
            branch_collections = []
            nested_collection_id = None
            self.add_error_as_exception(EnmApplicationError("All/some of the branch collections could not be created."))
        else:
            log.logger.debug("Successfully created branch collections.")
        return branch_collections, nested_collection_id

    def traverse_collections(self, user, root_custom_topology):
        """
        Traverse the topology and retrieve the collections.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param root_custom_topology: Collection object of root custom topology
        :type root_custom_topology:
        """
        try:
            log.logger.debug("Attempting to traverse the topology and retrieve the collections.")
            payload = {"parentId": root_custom_topology.id}
            for _ in range(1, self.NUM_BRANCH_COLLECTIONS + 1):
                response = search_collections(user, payload)
                branch_collection = json.loads(response.content)[0]
                log.logger.debug("Succesfully retrieved branch collection with id {0}"
                                 " and name {1}".format(branch_collection["id"],
                                                        branch_collection["name"]))
                payload = {"parentId": branch_collection["id"]}
            response = search_collections(user, payload)
            leaf_collections = json.loads(response.content)
            for leaf_collection in leaf_collections:
                root_custom_topology.get_collection_by_id(collection_id=leaf_collection["id"],
                                                          include_contents=True)
        except Exception:
            self.add_error_as_exception(
                EnmApplicationError("Unable to traverse the topology "
                                    "and retrieve the collections."))
        else:
            log.logger.debug("Successfully traversed the topology and retrieved the collections.")

    def cleanup_branch_collections(self, branch_collections, user):
        """
        Clean up branch collections.

        :param branch_collections: Branch collections to be cleaned up
        :type branch_collections: list
        :param user: ENM user
        :type user: `enm_user_2.User`
        """
        exception_count = 0
        log.logger.debug("Attempting to delete branch collections.")
        for branch_collection in branch_collections[::-1]:
            log.logger.debug("Attempting to delete branch collection - {0}.".format(branch_collection.name))
            try:
                branch_collection.delete()
                if branch_collection in self.teardown_list:
                    self.teardown_list.remove(branch_collection)
            except Exception as e:
                exception_count += 1
        if exception_count:
            self.add_error_as_exception(EnmApplicationError("Unable to delete {0} branch collections. "
                                                            "Most recent error is - {1}.".format(exception_count, e)))
        log.logger.debug("Completed attempt to delete branch collections.")

    def cleanup_root_custom_topology(self, root_custom_topology, user):
        """
        Clean up root custom topology.

        :param root_custom_topology: Root custom topology to be cleaned up
        :type root_custom_topology: `netex.Collection`
        :param user: ENM user
        :type user: `enm_user_2.User`
        """
        log.logger.debug("Attempting to delete root custom topology - {0}.".format(root_custom_topology.name))
        try:
            root_custom_topology.delete()
            if root_custom_topology in self.teardown_list:
                self.teardown_list.remove(root_custom_topology)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        log.logger.debug("Completed attempt to delete root custom topology - {0}.".format(root_custom_topology.name))

    def cleanup(self, root_custom_topology, branch_collections, leaf_collections, user):
        """
        Clean up the objects created by profile.

        :param root_custom_topology: Root custom topology to be cleaned up
        :type root_custom_topology: `netex.Collection`
        :param branch_collections: Branch collections to be cleaned up
        :type branch_collections: list
        :param leaf_collections: Leaf collections to be cleaned up
        :type leaf_collections: list
        :param user: ENM user
        :type user: `enm_user_2.User`
        """
        log.logger.debug("Attempting to clean up the objects created by profile.")
        try:
            self.delete_collections(leaf_collections, user)
            self.cleanup_branch_collections(branch_collections, user)
            self.cleanup_root_custom_topology(root_custom_topology, user)
        except Exception:
            self.add_error_as_exception(EnmApplicationError("Cleanup could not be performed successfully."))
        else:
            log.logger.debug("Attempt completed to clean up the objects created by profile.")


class Netex07Flow(Netex05Flow):
    """
    Profile flow for NETEX_07
    """
    NUM_BRANCH_COLLECTIONS = 6
    NUM_LEAF_COLLECTIONS = 400
    LEVEL_LEAF_COLLECTIONS = 2
    NUM_ELEMENTS_IN_COLLECTION = 500

    def execute_flow(self):
        """
        Executes the Netex 07 flow.
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        export_file_name = "{0}_export_file.zip".format(self.NAME)
        self.state = "RUNNING"
        while self.keep_running():
            self.cleanup_leaf_branch_topology(user)
            collection_ids_to_export = self.create_topology_and_collections(user=user)
            session_id = self.export_collections(user=user, collection_ids_to_export=collection_ids_to_export)
            if session_id:
                self.download_collections(user=user, session_id=session_id, export_file_name=export_file_name)
                self.cleanup_leaf_branch_topology(user)
                self.import_collections(user, export_file_name)
            else:
                self.add_error_as_exception(
                    EnmApplicationError("Unable to retireve session id while exporting "
                                        "collections. Will retry in next iteration."))
            log.logger.debug("Sleep for 120 seconds before clean up.")
            time.sleep(120)
            self.cleanup_leaf_branch_topology(user)
            self.cleanup_teardown()
            self.sleep()

    def export_collections(self, user, collection_ids_to_export):
        """
        Export collections from root of the topology and log the time taken.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param collection_ids_to_export: collection ids to be exported
        :type collection_ids_to_export: list
        :raises EnmApplicationError: when there is no session id
        :return: session id for collection export
        :rtype: str
        """
        session_id = None
        try:
            start_time = time.time()
            session_id = netex.initiate_export_collections(profile=self, user=user,
                                                           collection_ids=collection_ids_to_export,
                                                           nested=True)
            if session_id:
                netex.retrieve_export_collection_status(profile=self, user=user, session_id=session_id)
                end_time = time.time()
                time_taken = end_time - start_time
                log.logger.debug("Export of collections of collections using custom topology "
                                 "is completed in {0} seconds".format(time_taken))
            else:
                raise EnmApplicationError("Unable to get the session id to export collections.")
        except Exception as e:
            self.add_error_as_exception(e)
        return session_id

    def create_topology_and_collections(self, user):
        """
        Create topology and required collections.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :raises EnmApplicationError : when root topology or branch collections
                                      could not be created.
        :return: collection id of root custom topology in a list
        :rtype: list
        """
        collection_ids_to_export = []
        try:
            root_custom_topology = self.create_root_custom_topology(user)
            if not root_custom_topology:
                raise EnmApplicationError("Root custom topology could not be created.")

            branch_collections = self.create_branch_collections(user, root_custom_topology.id, self.NUM_BRANCH_COLLECTIONS)
            if not branch_collections:
                raise EnmApplicationError("Branch collections could not be created.")

            self.create_required_leaf_collections(user, branch_collections)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
        else:
            collection_ids_to_export.append(root_custom_topology.id)
        return collection_ids_to_export

    def create_branch_collections(self, user, branch_collection_id, num_collections):
        """
        Create branch collections.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param branch_collection_id: id of parent branch collection
        :type branch_collection_id: str
        :param num_collections: number of collections to be created
        :type num_collections: int
        :return: Tuple containing list of branch collections created and id of the bottom most branch collection
        :rtype: tuple
        """
        branch_collections = []
        log.logger.debug("Attempting to create branch collections.")
        try:
            for _ in range(1, num_collections + 1):
                collection = Collection(user, name="level_{0}_branch_{1}".format(1, self.identifier),
                                        type="BRANCH", parent_ids=[branch_collection_id])
                collection.create()
                branch_collections.append(collection)
                self.teardown_list.append(collection)
        except Exception:
            branch_collections = []
            self.add_error_as_exception(EnmApplicationError("All/some of the branch collections could not be created."))
        else:
            log.logger.debug("Successfully created branch collections.")
        return branch_collections

    def create_required_leaf_collections(self, user, branch_collections):
        """
        Create leaf collections.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param branch_collections: branch collection objects
        :type branch_collections: `netex.Collection`
        :raises EnmApplicationError: if po ids are not retrieved from the search
        :return: list of leaf collections
        :rtype: list
        """
        po_ids = self.get_poids_from_search(user)
        if not po_ids:
            raise EnmApplicationError("Unable to get po ids from the search to create leaf collections.")
        required_num_leaf_collections = self.NUM_LEAF_COLLECTIONS
        num_branch_collections = len(branch_collections)
        chunk_size = required_num_leaf_collections / num_branch_collections
        chunk_size_list = [chunk_size] * num_branch_collections
        for i in range(required_num_leaf_collections % num_branch_collections):
            chunk_size_list[i] = chunk_size + 1
        for branch_collection, final_chunk_size in zip(branch_collections, chunk_size_list):
            leaf_collections = self.create_regular_collections_for_leaf(user,
                                                                        num_collections=final_chunk_size,
                                                                        level=self.LEVEL_LEAF_COLLECTIONS,
                                                                        parent_id=branch_collection.id,
                                                                        poids=po_ids)
            if not leaf_collections:
                self.add_error_as_exception(
                    EnmApplicationError("Leaf collections could not be created for the branch collection "
                                        "with id - {0}.".format(branch_collection.id)))
        return leaf_collections

    def download_collections(self, user, session_id, export_file_name):
        """
        Download the exported collections and create export file for collections.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param session_id: session id for collection export
        :type session_id: str
        :param export_file_name: File name for the export
        :type export_file_name: str
        """
        try:
            download_response = download_exported_collections(user, session_id)
            download_data = download_response.content
            create_export_dir_and_file(download_data, export_file_name)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))

    def import_collections(self, user, export_file_name):
        """
        Import collections from root of the topology and log the time taken.

        :param user: ENM user
        :type user: `enm_user_2.User`
        :param export_file_name: Name of the file exported earlier.
        :type export_file_name: str
        :raises EnmApplicationError: when there is no session id
        """
        try:
            start_time = time.time()
            session_id = initiate_import_collections(user, export_file_name)
            if session_id:
                retrieve_import_collection_status(profile=self, user=user, session_id=session_id)
                end_time = time.time()
                time_taken = end_time - start_time
                log.logger.debug("Import of collections of collections using custom topology "
                                 "is completed in {0} seconds".format(time_taken))
            else:
                raise EnmApplicationError("Unable to get the session id to import collections.")
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError(e))
