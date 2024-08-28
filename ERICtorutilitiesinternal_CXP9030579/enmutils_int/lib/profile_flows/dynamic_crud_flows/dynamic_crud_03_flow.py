import copy
import time
from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironWarning
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.dynamic_crud import (SINGLE_MO_ALL_ATTRIBUTES_URL, DYNAMIC_CRUD_03_POST_PAYLOAD,
                                           DYNAMIC_CRUD_03_PUT_PAYLOAD)
from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow import DynamicCrudFlow, CMEDIT_GET_CELL_CMD

REQ_1_2_3_EUTRANETWORK_CMD = "EUtraNetwork.*"
DYNAMIC_CRUD_03_MO = "EUtranFrequency"
MO_START = 17
MO_END = 25
INTERMEDIATE_SLEEP = 30 * 60


class DynamicCrud03Flow(DynamicCrudFlow):
    """
    Class for flow of DYNAMIC_CRUD_03.
    """

    def execute_flow(self):
        """
        Executes the flow for the profile.
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        req_counts = self.REQ_COUNTS
        number_of_threads = self.NUMBER_OF_THREADS
        self.sleep_until_next_scheduled_iteration()
        self.state = "RUNNING"
        while self.keep_running():
            mos_for_workers = self.flow_setup(user, req_counts, number_of_threads)
            if mos_for_workers:
                self.create_update_delete_flow(mos_for_workers, number_of_threads, user)
            else:
                self.add_error_as_exception(EnvironWarning("Unable to prepare data required to execute this iteration."
                                                           "Will retry in the next iteration."))
            self.sleep_until_next_scheduled_iteration()
            self.exchange_nodes()

    def create_update_delete_flow(self, mos_for_workers, number_of_threads, user):
        """
        Flow to create threads to create, update and delete required MOs.

        :param mos_for_workers: MO data in the format required for threads to be executed
        :type mos_for_workers: list
        :param number_of_threads: Number of threads
        :type number_of_threads: int
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user],
                                        last_error_only=True)
        teardown_object = partial(picklable_boundmethod(self.cleanup_existing_mos), user)
        self.teardown_list.append(teardown_object)
        log.logger.debug("Sleeping for {0} seconds before update.".format(INTERMEDIATE_SLEEP))
        time.sleep(INTERMEDIATE_SLEEP)
        self.reestablish_session(user)
        self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user],
                                        func_ref=self.update_task_set, last_error_only=True)
        log.logger.debug("Sleeping for {0} seconds before deletion.".format(INTERMEDIATE_SLEEP))
        time.sleep(INTERMEDIATE_SLEEP)
        self.reestablish_session(user)
        self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user],
                                        func_ref=self.delete_task_set, last_error_only=True)
        self.teardown_list.remove(teardown_object)
        time.sleep(10)
        self.cleanup_existing_mos(user)

    def flow_setup(self, user, req_counts, number_of_threads):
        """
        Method to carry out the setup required to execute the POST, PUT and DELETE requests.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param req_counts: Number of objects required for POST, PUT and DELETE requests depending on the size of the
                           network
        :type req_counts: dict
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :return: MO data in the format required for threads to be executed
        :rtype: list
        """
        self.reestablish_session(user)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "lte_cell_type", "netsim", "primary_type"])
        filtered_nodes = self.get_filtered_nodes_per_host(nodes)
        self.cleanup_existing_mos(user)
        mos_for_workers = self.prepare_data(user, filtered_nodes, req_counts, number_of_threads)
        return mos_for_workers

    def remove_existing_mo(self, user, existing_mo_list):
        """
        Method to remove the existing MOs.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param existing_mo_list: List of existing MO
        :type existing_mo_list: list
        """
        log.logger.debug("Removing existing MOs.")
        for mo in existing_mo_list:
            url = self.get_final_path_for_url(mo)
            remove_response = self.delete_given_url(user, url)
            log.logger.debug("MO {0} removed successfully.".format(mo)
                             if hasattr(remove_response, "status_code") and remove_response.status_code == 200
                             else "MO {0} not removed.".format(mo))

    def prepare_data(self, user, nodes, req_counts, number_of_threads):
        """
        Prepare the required data for this iteration.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :param req_counts: Number of requests for various types of requests depending on the size of the network
        :type req_counts: dict
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :return: MO data in the format required for threads to be executed
        :rtype: list
        """
        log.logger.debug("Starting attempt to prepare the required data for this iteration.")
        mos_for_workers_req_1_2_3 = self.prepare_data_for_req("REQ_1_2_3", user, nodes,
                                                              req_counts, number_of_threads, False)
        mos_for_workers = mos_for_workers_req_1_2_3
        log.logger.debug("Completed attempt to prepare the required data for this iteration.")
        return mos_for_workers

    def configure_mo_data(self, req, user, nodes):
        """
        Generate or reuse data for each type of request.

        :param req: Identifier for the request type
        :type req: str
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :return: MO data
        :rtype: dict
        """
        log.logger.debug("Starting attempt to generate or reuse data for - {0}.".format(req))
        mo_data = self.get_mo_data_req(req, user, nodes)
        log.logger.debug("Completed attempt to generate or reuse data for - {0}.".format(req))
        return mo_data

    def get_mo_data_req(self, req, user, nodes):
        """
        Generate data through cmedit commands for a specific type of request.

        :param req: Identifier for the request type
        :type req: str
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :return: MO data for each type of request
        :rtype: dict
        """
        log.logger.debug("Starting attempt to generate data through cmedit commands for - {0}.".format(req))
        mo_data = {}
        for node in nodes:
            list_of_fdns = []
            node_id = node.node_id
            try:
                response = user.enm_execute(CMEDIT_GET_CELL_CMD.format(node_id, REQ_1_2_3_EUTRANETWORK_CMD))
                mo_data[node_id] = self.get_random_mo_data(response, list_of_fdns)
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.debug("Completed attempt to generate data through cmedit commands for - {0}.".format(req))
        return mo_data

    @staticmethod
    def get_final_path_for_url(mo_path):  # pylint: disable=arguments-differ
        """
        Form complete request URL for the given MO.

        :param mo_path: MO path
        :type mo_path: str
        :return: Complete request URL
        :rtype: str
        """
        base_url_for_mo = SINGLE_MO_ALL_ATTRIBUTES_URL
        final_path_for_url = base_url_for_mo.format(mo_path)
        return final_path_for_url

    @staticmethod
    def task_set(worker, profile, user):  # pylint: disable=arguments-differ
        """
        Method to make the POST requests.

        :param worker: tuple of request type and path of MO on which request is executed
        :type worker: tuple
        :param profile: limit for each user consuming events
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        mo_path = worker
        final_path_for_url = profile.get_final_path_for_url(mo_path)
        for i in range(MO_START, MO_END):
            payload_mo = copy.deepcopy(DYNAMIC_CRUD_03_POST_PAYLOAD)
            payload_mo[DYNAMIC_CRUD_03_MO][0]["id"] = "{0}_{1}".format(
                profile.NAME, i)
            payload_mo[DYNAMIC_CRUD_03_MO][0]["attributes"]["userLabel"] = "{0}_{1}".format(
                profile.NAME, i)
            payload_mo[DYNAMIC_CRUD_03_MO][0]["attributes"]["arfcnValueEUtranDl"] = i
            profile.post_to_url_with_payload(user, final_path_for_url, payload_mo)

    @staticmethod
    def update_task_set(worker, profile, user):  # pylint: disable=arguments-differ
        """
        Method to make the PUT requests.

        :param worker: tuple of request type and path of MO on which request is executed
        :type worker: tuple
        :param profile: limit for each user consuming events
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        mo_path = worker
        final_path_for_url = profile.get_final_path_for_url(mo_path)
        for i in range(MO_START, MO_END):
            payload_mo = copy.deepcopy(DYNAMIC_CRUD_03_PUT_PAYLOAD)
            payload_mo[DYNAMIC_CRUD_03_MO]["attributes"]["userLabel"] = "{0}_{1}_modified".format(
                profile.NAME, i)
            url_to_update = "{0}/{1}={2}".format(final_path_for_url, DYNAMIC_CRUD_03_MO, "{0}_{1}".format(
                profile.NAME, i))
            profile.put_to_url_with_payload(user, url_to_update, payload_mo)

    @staticmethod
    def delete_task_set(worker, profile, user):  # pylint: disable=arguments-differ
        """
        Method to make the DELETE requests.

        :param worker: tuple of request type and path of MO on which request is executed
        :type worker: tuple
        :param profile: limit for each user consuming events
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        mo_path = worker
        final_path_for_url = profile.get_final_path_for_url(mo_path)
        for i in range(MO_START, MO_END):
            url_to_delete = "{0}/{1}={2}".format(final_path_for_url, DYNAMIC_CRUD_03_MO, "{0}_{1}".format(
                profile.NAME, i))
            profile.delete_given_url(user, url_to_delete)
