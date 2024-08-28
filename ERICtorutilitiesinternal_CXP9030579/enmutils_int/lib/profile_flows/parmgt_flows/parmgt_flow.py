import itertools
import math
import random
import time
from collections import defaultdict
from datetime import datetime, date, timedelta
from functools import partial
from requests import HTTPError, ConnectionError
from enmutils.lib import log
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.netex import get_pos_by_poids
from enmutils_int.lib.node_security import check_sync_and_remove
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.parameter_management import temporary_query_for_mo_class_mapping, update_attributes

SEARCH_QUERY_DICT = {
    "cran": "select NRCellCU with attr qHyst, threshServingLowP from node type Shared-CNF",
    "4g": ("select ENodeBFunction with attr combCellSectorSelectThreshRx, "
           "combCellSectorSelectThreshTx from node type RadioNode "
           "filter by radioAccessTechnology containing 4G"),
    "5g": ("select NRCellDU with attr nRPCI, endcUlNrQualHyst from node type RadioNode "
           "filter by radioAccessTechnology containing 5G")
}
ATTRIBUTE_MAPPINGS_DICT = {"cran": [{"attributeNames": ["qHyst",
                                                        "threshServingLowP"],
                                     "moType": "NRCellCU"}],
                           "4g": [{"attributeNames": ["combCellSectorSelectThreshRx",
                                                      "combCellSectorSelectThreshTx"],
                                   "moType": "ENodeBFunction"}],
                           "5g": [{"attributeNames": ["nRPCI",
                                                      "endcUlNrQualHyst"],
                                   "moType": "NRCellDU"}]}
ATTRIBUTE_VALUE = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]


class ParMgt01Flow(GenericFlow):
    def __init__(self, *args, **kwargs):
        self.synced = None
        super(ParMgt01Flow, self).__init__(*args, **kwargs)

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        try:
            self.synced, _ = check_sync_and_remove(self.get_nodes_list_by_attribute(), users[0])
        except Exception:
            self.add_error_as_exception(EnmApplicationError("Unable to get sync status for the nodes "
                                                            "and remove nodes which are not in sync."))
        while self.keep_running():
            try:
                self.exchange_nodes_and_check_sync(user=users[0])
            except Exception:
                self.add_error_as_exception(EnmApplicationError("Unable to exchange nodes or get sync status for "
                                                                "the nodes and remove nodes which are not in sync."))
            self.set_schedule_time()
            self.sleep_until_time()
            if self.synced:
                user_node_data = self.process_po_data(users=users, synced=self.synced)
                if user_node_data:
                    # Removing previously added teardown for reset_attributes
                    self.remove_partial_items_from_teardown_list()
                    worker_data = self.convert_user_node_data_for_worker(user_node_data)
                    # Adding teardown for reset_attributes with latest data
                    self.teardown_list.append(partial(picklable_boundmethod(self.reset_attributes), users[0],
                                                      worker_data))
                    self.create_and_execute_threads(worker_data, len(users), args=[self])
            else:
                self.add_error_as_exception(
                    EnvironError("No synced nodes to run profile. "
                                 "Will exchange nodes after about 24 hours and retry."))
                # Sleeping for 23 hours and 40 minutes and will check
                # whether the time to exchange and check sync
                # status of nodes occurs in the next few iterations
                log.logger.info("Sleeping for 23 hours and 40 minutes")
                time.sleep(self.DAILY_SLEEP)

    @staticmethod
    def convert_user_node_data_for_worker(user_node_data):
        """
        Convert user node data to a format that can be used by task set
        :param user_node_data: user and corresponding data for persistent object to be updated
        :type user_node_data: dict
        :return: list of tuples of user, persistent object data along with
                 type of node i.e. 4g or 5g or cran to be used by task set
        :rtype: list
        """
        user_node_data_4g = user_node_data.get('4g', {})
        user_node_data_5g = user_node_data.get('5g', {})
        user_node_data_cran = user_node_data.get('cran', {})
        user_node_data_for_worker = defaultdict(list)
        for d in (user_node_data_4g, user_node_data_5g, user_node_data_cran):
            for key, value in d.items():
                user_node_data_for_worker[key].append(value)
        worker_dict = dict(user_node_data_for_worker)
        worker_data = [(k, sum(v, [])) for k, v in worker_dict.items()]
        return worker_data

    def set_schedule_time(self):
        """
        Sets SCHEDULED_TIMES
        """
        start_time = datetime.strptime(self.SCHEDULED_TIMES_STRINGS[0], '%H:%M:%S').replace(year=datetime.now().year,
                                                                                            month=datetime.now().month,
                                                                                            day=datetime.now().day)
        setattr(self, 'SCHEDULED_TIMES', [start_time + timedelta(minutes=minute) for minute in
                                          xrange(0, self.NUMBER_OF_ITERATIONS * self.TIME_IN_MINUTES_BETWEEN_ITERATIONS,
                                                 self.TIME_IN_MINUTES_BETWEEN_ITERATIONS)])

    def exchange_nodes_and_check_sync(self, user):
        """
        Exchange the nodes if there are no synced nodes 24 hours earlier.
        Check the sync status of all nodes and remove unsynced nodes every 24 hours
        irrespective of whether there are synced nodes or not earlier.
        :type user: `enm_user_2.User`
        :param user:`enm_user_2.User to check sync status of the nodes
        """
        today = date.today()
        time_to_check_sync = self.start_time.replace(year=today.year,
                                                     month=today.month,
                                                     day=today.day)
        if 0 < (time_to_check_sync - datetime.now()).total_seconds() < self.TIME_IN_MINUTES_BETWEEN_ITERATIONS * 60:
            if not self.synced:
                log.logger.info("Exchanging the nodes if there are no synced nodes 24 hours earlier.")
                self.exchange_nodes()
            log.logger.info("Check the sync status of all nodes and remove unsynced nodes every 24 hours"
                            " irrespective of whether there are synced nodes or not earlier.")
            self.synced, _ = check_sync_and_remove(self.get_nodes_list_by_attribute(), user)

    def process_po_data(self, users, synced):
        """
        Retrieve and process PO data for the nodes selected and synced
        :type users: list
        :param users: list of `enm_user_2.User` objects
        :type synced: list
        :param synced: list of `enmutils.lib.enm_node.Node` objects selected by profile and are in synchronized state
.
        :rtype: user_node_data: list
        :return: user_node_data: list of tuples of user and corresponding POs to be modified
        """
        user_node_data = {}
        list_of_selected_node_names = [node.node_id for node in synced]
        po_id_dict = {}
        for gen, query in SEARCH_QUERY_DICT.items():
            po_id_dict[gen] = self.get_po_ids_for_selected_nodes(user=users[0],
                                                                 query=query,
                                                                 node_names=list_of_selected_node_names,
                                                                 gen=gen)
        log.logger.debug(
            "Before filter Expected 4g and 5g po data length {0} and {1} and cran {2}".format(
                len(po_id_dict.get('4g', [])),
                len(po_id_dict.get('5g', [])),
                len(po_id_dict.get('cran', []))))
        expected_po_id_dic = self.get_expected_po_data(po_id_dict)
        log.logger.debug(
            "Expected 4g and 5g po data length {0} and {1} and cran {2}".format(len(expected_po_id_dic.get('4g', [])),
                                                                                len(expected_po_id_dic.get('5g', [])),
                                                                                len(expected_po_id_dic.get('cran',
                                                                                                           []))))
        po_list = []
        for gen, po_ids in expected_po_id_dic.items():
            if not po_ids:
                continue
            # Split po_ids into chunks of 250 (maximum number supported by getPosByPoIds)
            # and combine the output of getPosByPoIds
            for po_ids_chunk in chunks(po_ids, 250):
                try:
                    pos_response = get_pos_by_poids(users[0], po_ids_chunk,
                                                    attributeMappings=ATTRIBUTE_MAPPINGS_DICT[gen])
                    po_content = pos_response.json()
                except (HTTPError, ConnectionError) as e:
                    self.add_error_as_exception(
                        EnmApplicationError("Error in fetching persistent object data {0}".format(str(e))))
                except Exception as e:
                    self.add_error_as_exception(e)
                else:
                    po_list.extend(po_content)
            if po_list:
                # Distribute persistent object data for all persistent object ids to the users
                user_node_data[gen] = self.get_user_node_data(users=users, po_list=po_list, gen=gen)
            po_list = []
        return user_node_data

    def get_expected_po_data(self, po_id_dict):
        """
         Retrieve and process PO data for the attribute selected
        :type po_id_dict: dict
        :param po_id_dict: dict of object
        :rtype: expected_po_id_dic: dict
        :return: expected_po_id_dic: dict of attribute object
        """
        expected_po_length = 1400
        total_node = sum(len(val) for val in po_id_dict.values())
        try:
            node_ratio = float(expected_po_length) / total_node
        except Exception as e:
            log.logger.debug(e)
        if total_node > expected_po_length:
            initial_expected_po_id_dic = {key: max(1, int(math.floor(len(val) * node_ratio))) if len(val) > 0 else 0 for
                                          key, val in po_id_dict.items()}
            initial_total_length = sum(initial_expected_po_id_dic.values())
            adjusted_expected_po_id_dic = initial_expected_po_id_dic.copy()
            remaining = expected_po_length - initial_total_length
            keys = list(adjusted_expected_po_id_dic.keys())
            for rem_po in range(remaining):
                adjusted_expected_po_id_dic[keys[rem_po % len(keys)]] += 1
            required_data = {key: po_id_dict[key][:val] for key, val in adjusted_expected_po_id_dic.items()}
            return required_data
        else:
            return po_id_dict

    def get_po_ids_for_selected_nodes(self, user, query, node_names, gen):
        """
        Get persistent object ids for the selected nodes in the profile matching with
        temporary_query_for_mo_class_mapping response.
        :type user: `enm_user_2.User`
        :param user: User who will create the job
        :type query: str
        :param query: Search query to be performed
        :type node_names: list
        :param node_names: list of selected node names
        :type gen: str
        :param gen: 4g or 5g or cran
        :rtype: po_ids: list
        :return: po_ids: list of PO ids
        """
        po_ids = []
        try:
            log.logger.info("Get persistent object ids for the selected nodes in the profile matching with "
                            "temporary_query_for_mo_class_mapping response.")
            mo_mapping = temporary_query_for_mo_class_mapping(user, query)
            for i in mo_mapping["moDetails"]:
                for j in i["moTypes"][ATTRIBUTE_MAPPINGS_DICT[gen][0]["moType"]]:
                    if j["nodeName"] in node_names:
                        po_ids.append(j["poId"])
        except (HTTPError, ConnectionError) as e:
            self.add_error_as_exception(
                EnmApplicationError("Unable to get managed object mapping "
                                    "due to {0}".format(str(e))))
        except Exception as e:
            self.add_error_as_exception(e)
        return po_ids

    def get_user_node_data(self, users, po_list, gen):
        """
        Distribute persistent objects for each user
        :type users: list
        :param users: list of `enm_user_2.User` objects
        :type po_list: list
        :param po_list: list of persistent object ids for the selected nodes
        :type gen: str
        :param gen: 4g or 5g or cran
        :rtype: user_node_data: list
        :return: user_node_data: list of tuples of user and corresponding POs to be modified
        """
        log.logger.info("Distribute persistent objects for each user")
        po_list_per_user = [po_list[i:i + int(len(po_list) / self.NUM_USERS) or 1]
                            for i in range(0, len(po_list), int(len(po_list) / self.NUM_USERS) or 1)]
        user_node_data = dict(zip(users, [[(po_data, gen) for po_data in po_list] for po_list in po_list_per_user]))
        return user_node_data

    def reset_attributes(self, user, user_node_data):
        """
        Reset modified attributes back to their original values
        :type user: `enm_user_2.User`
        :param user: User who will create the job
        :type user_node_data: list
        :param user_node_data: list of tuples of user and corresponding POs to be modified
        """
        log.logger.info("Reset modified attributes back to their original values - started")
        po_list = list(itertools.chain(*[_[1] for _ in user_node_data]))
        for po_data in po_list:
            try:
                update_attributes(user, po_data[0],
                                  attributes=[{"key": ATTRIBUTE_MAPPINGS_DICT[po_data[1]][0]["attributeNames"][0],
                                               "value": po_data[0]["attributes"][
                                                   ATTRIBUTE_MAPPINGS_DICT[po_data[1]][0]["attributeNames"][0]],
                                               "datatype": "INTEGER"},
                                              {"key": ATTRIBUTE_MAPPINGS_DICT[po_data[1]][0]["attributeNames"][1],
                                               "value": po_data[0]["attributes"][
                                                   ATTRIBUTE_MAPPINGS_DICT[po_data[1]][0]["attributeNames"][1]],
                                               "datatype": "INTEGER"}])
            except HTTPError as e:
                self.add_error_as_exception(
                    EnvironError("Error in updating required attributes for po id "
                                 "{0} : {1}, node {2} may not be in "
                                 "sync".format(po_data[0]["poId"], str(e), po_data[0]["mibRootName"])))
            except ConnectionError as e:
                self.add_error_as_exception(
                    EnmApplicationError("Error in updating required attributes for "
                                        "po id {0} : {1}".format(po_data[0]["poId"], str(e))))
            except KeyError as e:
                self.add_error_as_exception(
                    EnvironError("Required attributes are not found in selected nodes for "
                                 "po data {0}, error is {1}".format(str(po_data[0]), str(e))))
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.info("Reset modified attributes back to their original values - completed")

    @staticmethod
    def task_set(worker, profile):
        """
        Task set for use with thread queue
        :type worker: list
        :param worker: list of tuples of user and corresponding persistent objects to be modified
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        user, po_list = worker
        timeout = int(user.username.split("_u")[1]) * 10  # 10 second delay between users
        time.sleep(timeout)
        for po_data in po_list:
            try:
                update_attributes(user, po_data[0],
                                  attributes=[{"key": ATTRIBUTE_MAPPINGS_DICT[po_data[1]][0]["attributeNames"][0],
                                               "value": random.choice(ATTRIBUTE_VALUE) if po_data[1] == 'cran' else random.randint(
                                                   0, 1000),
                                               "datatype": "INTEGER"},
                                              {"key": ATTRIBUTE_MAPPINGS_DICT[po_data[1]][0]["attributeNames"][1],
                                               "value": random.randint(1, 60),
                                               "datatype": "INTEGER"}])
            except HTTPError as e:
                profile.add_error_as_exception(
                    EnvironError("Error in updating required attributes for po id "
                                 "{0} : {1}, node {2} may not be in "
                                 "sync".format(po_data[0]["poId"], str(e), po_data[0]["mibRootName"])))
            except ConnectionError as e:
                profile.add_error_as_exception(
                    EnmApplicationError("Error in updating required attributes for "
                                        "po id {0} : {1}".format(po_data[0]["poId"], str(e))))
            except KeyError as e:
                profile.add_error_as_exception(
                    EnvironError("Required attributes are not found in selected nodes for "
                                 "po data {0}, error is {1}".format(str(po_data[0]), str(e))))
            except Exception as e:
                profile.add_error_as_exception(e)
