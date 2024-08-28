from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.dynamic_crud import SINGLE_MO_ALL_ATTRIBUTES_URL
from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow import DynamicCrudFlow


class DynamicCrud04Flow(DynamicCrudFlow):
    """
    Class for flow of DYNAMIC_CRUD_04.
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
            nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "lte_cell_type"])
            mos_for_workers = self.prepare_data(user, nodes, req_counts, number_of_threads)
            mos_for_workers = list(chunks(mos_for_workers, sum(req_counts.values()) / number_of_threads))
            if mos_for_workers:
                self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user],
                                                last_error_only=True)
            else:
                self.add_error_as_exception(EnvironError("Unable to prepare data required to execute this iteration."
                                                         "Will retry in the next iteration."))
            self.sleep_until_next_scheduled_iteration()
            self.exchange_nodes()

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
                                                              req_counts, number_of_threads)
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
        mo_data = self.get_mo_data_req_based_on_cell_type(user, nodes)
        log.logger.debug("Completed attempt to generate data through cmedit commands for - {0}.".format(req))
        return mo_data

    @staticmethod
    def get_final_path_for_url(req, mo_path):
        """
        Form complete request URL for the given MO.

        :param req: Identifier for the request type
        :type req: str
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
        Method to make the REST request

        :param worker: list of request type and path of MO on which request is executed
        :type worker: list
        :param profile: limit for each user consuming events
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        for req_mo in worker:
            req, mo_path = req_mo
            final_path_for_url = profile.get_final_path_for_url(req, mo_path)
            profile.get_given_url(user, final_path_for_url)

    def remove_existing_mo(self, user, existing_mo_list):  # pylint: disable=W0223
        """
        Method to remove the existing MOs.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param existing_mo_list: List of existing MO
        :type existing_mo_list: list
        """
        pass
