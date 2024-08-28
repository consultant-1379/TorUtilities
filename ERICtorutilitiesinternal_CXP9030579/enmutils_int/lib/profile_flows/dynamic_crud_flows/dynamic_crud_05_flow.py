import time
from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironWarning
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.dynamic_crud import SINGLE_MO_ALL_ATTRIBUTES_URL
from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow import DynamicCrudFlow, CMEDIT_GET_CELL_CMD

EUTRANETWORK_CMD = "EUtraNetwork.*"
ADD_OPERATION = "add"
REMOVE_OPERATION = "remove"
REMOVE_PAYLOAD = [{"op": "remove"}]
INTERMEDIATE_SLEEP = 30 * 60


class DynamicCrud05Flow(DynamicCrudFlow):
    """
    Class for flow of DYNAMIC_CRUD_05.
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
            self.reestablish_session(user)
            mos_for_workers = self.flow_setup(user, req_counts, number_of_threads)
            if mos_for_workers:
                self.add_remove_obj(user, mos_for_workers, number_of_threads)
            else:
                self.add_error_as_exception(EnvironWarning("Unable to prepare data required to execute this iteration. "
                                                           "Will retry in the next iteration."))
            self.sleep_until_next_scheduled_iteration()
            self.exchange_nodes()

    def flow_setup(self, user, req_counts, number_of_threads):
        """
        Method to carry out the setup required to execute the PATCH request

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param req_counts: Number of objects required for PATCH request depending on the size of the network
        :type req_counts: dict
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :return: MO data in the format required for threads to be executed
        :rtype: list
        """
        retry = 1
        max_retries = 3
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "lte_cell_type", "netsim", "primary_type"])
        while retry <= max_retries:
            filtered_nodes = self.get_filtered_nodes_per_host(nodes)
            if filtered_nodes:
                self.cleanup_existing_mos(user)
                mos_for_workers = self.prepare_data(user, filtered_nodes, req_counts, number_of_threads)
                return mos_for_workers
            else:
                retry += 1
        self.add_error_as_exception(EnvironWarning("Unable to get filtered nodes"))
        return []

    def remove_existing_mo(self, user, existing_mo_list):
        """
        Method to remove the existing MOs

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param existing_mo_list: List of existing MO
        :type existing_mo_list: list
        """
        log.logger.debug("Removing existing MOs")
        for mo in existing_mo_list:
            url = self.get_final_path_for_url(mo)
            remove_response = self.patch_with_payload(user, url, REMOVE_PAYLOAD)
            log.logger.debug("MO {0} removed successfully.".format(mo)
                             if hasattr(remove_response, "status_code") and remove_response.status_code == 200
                             else "MO {0} not removed.".format(mo))

    def add_remove_obj(self, user, mos_for_workers, number_of_threads):
        """
        Method to add and remove the objects through PATCH request

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :param mos_for_workers: MO data in the format required for threads to be executed
        :type mos_for_workers: list
        """
        self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user, ADD_OPERATION])
        teardown_object = partial(picklable_boundmethod(self.cleanup_existing_mos), user)
        self.teardown_list.append(teardown_object)
        log.logger.debug("Sleeping for {0} seconds before deletion.".format(INTERMEDIATE_SLEEP))
        time.sleep(INTERMEDIATE_SLEEP)
        self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user, REMOVE_OPERATION])
        self.teardown_list.remove(teardown_object)

    def prepare_data(self, user, nodes, req_counts, number_of_threads):
        """
        Prepare the required data for this iteration.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :param req_counts: Number of objects required for PATCH request depending on the size of the network
        :type req_counts: dict
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :return: MO data in the format required for threads to be executed
        :rtype: list
        """
        log.logger.debug("Starting attempt to prepare the required data for this iteration.")
        mos_for_workers = self.prepare_data_for_req_obj("PATCH", user, nodes, req_counts)
        log.logger.debug("Completed attempt to prepare the required data for this iteration.")
        return mos_for_workers

    def prepare_data_for_req_obj(self, req, user, nodes, req_counts):
        """
        Prepare the required data for a specific type of request.

        :param req: Identifier for the request type
        :type req: str
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :param req_counts: Number of requests for various types of requests depending on the size of the network
        :type req_counts: dict

        :return: Required data for a specific type of request
        :rtype: list
        """

        log.logger.debug("Starting attempt to prepare the required data for {0} request.".format(req))
        mo_data = self.configure_mo_data(req, user, nodes)
        node_obj = []
        for _ in range(len(nodes)):
            node_obj.append(req_counts[req] / len(nodes))
        for i in range(req_counts[req] % len(nodes)):
            node_obj[i] = ((req_counts[req] / len(nodes)) + 1)
        mos_for_workers = [(node_obj[i], mo_data.values()[i]) for i in range(len(mo_data.values()))]
        log.logger.debug("Completed attempt to prepare the required data for {0} request.".format(req))
        return mos_for_workers

    def configure_mo_data(self, req, user, nodes):
        """
        Generate data for each type of request.

        :param req: Identifier for the request type
        :type req: str
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :return: MO data
        :rtype: dict
        """
        log.logger.debug("Starting attempt to generate data for {0} request.".format(req))
        mo_data = self.get_mo_data_req(req, user, nodes)
        log.logger.debug("Completed attempt to generate data for {0} request.".format(req))
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
        log.logger.debug("Starting attempt to generate data through cmedit commands for {0} request.".format(req))
        mo_data = {}
        for node in nodes:
            list_of_fdns = []
            node_id = node.node_id
            try:
                response = user.enm_execute(CMEDIT_GET_CELL_CMD.format(node_id, EUTRANETWORK_CMD))
                mo_data[node_id] = self.get_random_mo_data(response, list_of_fdns)
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.debug("Completed attempt to generate data through cmedit commands for {0} request.".format(req))
        log.logger.debug("MO data: {0}".format(mo_data))
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
    def generate_mo_payload(profile, req_obj, operation):
        """
        Method to generate all objects of node in one request
        :param profile: limit for each user consuming events
        :type profile: `flow_profile.FlowProfile`
        :param req_obj: object number
        :type req_obj: int
        :param operation: operation to be performed as a part of PATCH request
        :type operation: str

        :return: Payload consisting of MO data for PATCH request
        :rtype: list
        """
        payload_mo = []
        if operation == ADD_OPERATION:
            for obj in range(req_obj):
                payload_mo.append(dict())
                payload_mo[obj]["op"] = operation
                payload_mo[obj]["path"] = "/EUtranFrequency={0}_{1}".format(profile.NAME, obj + 1)
                value = {"id": "{0}_{1}".format(profile.NAME, obj + 1), "attributes": {"arfcnValueEUtranDl": 2}}
                payload_mo[obj]["value"] = value
        else:
            for obj in range(req_obj):
                payload_mo.append(dict())
                payload_mo[obj]["op"] = operation
                payload_mo[obj]["path"] = "/EUtranFrequency={0}_{1}".format(profile.NAME, obj + 1)
        log.logger.debug("Pay load is: {0}".format(payload_mo))
        return payload_mo

    @staticmethod
    def task_set(worker, profile, user, operation):  # pylint: disable=arguments-differ
        """
        Method to make the REST request

        :param worker: tuple of required objects count and path of MO on which request is executed
        :type worker: tuple
        :param profile: Profile object to execute the functionality
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param operation: operation to be performed as a part of PATCH request
        :type operation: str
        """
        req_obj, mo_path = worker
        final_path_for_url = profile.get_final_path_for_url(mo_path)
        payload = profile.generate_mo_payload(profile, req_obj, operation)
        profile.patch_with_payload(user, final_path_for_url, payload)
