import random
import time

from enmutils.lib import log
from enmutils.lib.headers import DYNAMIC_CRUD_PUT_HEADER
from enmutils.lib.exceptions import EnvironWarning
from enmutils.lib.headers import CRUD_PATCH_HEADER
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow

REQ_1_2_3_CELLS_CMD = ["EUtranCellTDD.*", "EUtranCellFDD.*", "NRCellDU.*"]
CMEDIT_GET_CELL_CMD = "cmedit get {0} {1}"
ALL_NODES = "*"
MO_CMD = "EUtranFrequency={0}*"


class DynamicCrudFlow(ShmFlow):
    """
    Common Flow for DYNAMIC CRUD profiles
    """

    def __init__(self, *args, **kwargs):
        self.mo_data_cells = None
        self.mo_data_nodes_4g = None
        self.mo_data_nodes_5g = None
        super(DynamicCrudFlow, self).__init__(*args, **kwargs)

    def get_given_url(self, user, url):
        """
        Perform GET request on given URL

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param url: URL of the request
        :type url: str
        """
        try:
            response = user.get(url, profile_name=self.NAME)
            response.raise_for_status()
        except Exception as e:
            self.add_error_as_exception(e)

    def patch_with_payload(self, user, url, payload):
        """
        Perform PATCH request on given URL

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param url: URL of the request
        :type url: str
        :param payload: Payload for the patch request
        :type payload: list

        :return: Returns the response
        :rtype: Response object
        """
        try:
            response = user.patch(url, profile_name=self.NAME, json=payload, headers=CRUD_PATCH_HEADER)
            response.raise_for_status()
            return response
        except Exception as e:
            self.add_error_as_exception(e)

    def post_to_url_with_payload(self, user, url, payload):
        """
        Perform POST request on given URL

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param url: URL of the request
        :type url: str
        :param payload: Payload for the post request
        :type payload: list

        :return: Returns the response
        :rtype: Response object
        """
        try:
            response = user.post(url, profile_name=self.NAME, json=payload)
            response.raise_for_status()
            return response
        except Exception as e:
            self.add_error_as_exception(e)

    def put_to_url_with_payload(self, user, url, payload):
        """
        Perform PUT request on given URL

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param url: URL of the request
        :type url: str
        :param payload: Payload for the put request
        :type payload: list

        :return: Returns the response
        :rtype: Response object
        """
        try:
            response = user.put(url, profile_name=self.NAME, json=payload, headers=DYNAMIC_CRUD_PUT_HEADER)
            response.raise_for_status()
            return response
        except Exception as e:
            self.add_error_as_exception(e)

    def delete_given_url(self, user, url):
        """
        Perform DELETE request on given URL

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param url: URL of the request
        :type url: str

        :return: Returns the response
        :rtype: Response object
        """
        try:
            response = user.delete_request(url, profile_name=self.NAME)
            response.raise_for_status()
            return response
        except Exception as e:
            self.add_error_as_exception(e)

    def execute_flow(self):
        """
        Executes the flow for the profile.
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        user = users[0]
        req_counts = self.REQ_COUNTS
        number_of_threads = self.NUMBER_OF_THREADS
        self.state = "RUNNING"
        while self.keep_running():
            nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "lte_cell_type"])
            mos_for_workers = self.prepare_data(user, nodes, req_counts, number_of_threads)
            if mos_for_workers:
                self.create_and_execute_threads(mos_for_workers, number_of_threads, args=[self, user],
                                                last_error_only=True)
            else:
                self.add_error_as_exception(EnvironWarning("Unable to prepare data required to execute this iteration."
                                                           "Will retry in the next iteration."))
            self.sleep_until_next_scheduled_iteration()
            self.exchange_nodes()
            self.reestablish_session(user)

    @staticmethod
    def reestablish_session(user):
        """
        Reestablish user session.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        log.logger.debug("Re-establish user session and then wait for 10 seconds.")
        user.open_session(reestablish=True)
        time.sleep(10)

    def remove_existing_mo(self, user, existing_mo_list):  # pylint: disable=W0223
        """
        Method to remove the existing MOs.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param existing_mo_list: List of existing MO
        :type existing_mo_list: list
        :raises NotImplementedError: If method is not overridden by derived class
        """
        raise NotImplementedError("This is a dummy method for remove_existing_mo that must be "
                                  "overridden in the derived class.")

    def cleanup_existing_mos(self, user):
        """
        Check if there are MOs created by this profile in previous iterations and attempt to clean them up
        if they exist.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        existing_mo_list = self.check_existing_mo(user)
        if existing_mo_list:
            log.logger.debug("Existing MOs: {0}".format(existing_mo_list))
            self.remove_existing_mo(user, existing_mo_list)

    def check_existing_mo(self, user):
        """
        Method to check if any EUtranFrequency MO of DYNAMIC_CRUD exist

        :param user: User who will make the requests
        :type user: `enm_user_2.User`

        :return: List of existing MOs
        :rtype: list
        """
        fdn_list = []
        existing_fdn_list = []
        log.logger.debug("Checking for existing MOs if any in {0} profile.".format(self.NAME))
        response = user.enm_execute(CMEDIT_GET_CELL_CMD.format(ALL_NODES, MO_CMD.format(self.NAME)))
        for line in response.get_output():
            if "FDN" in line:
                fdn_list.append(line)
        if not fdn_list:
            log.logger.debug("No existing MO available for {0} profile.".format(self.NAME))
        else:
            for fdn in fdn_list:
                existing_fdn_list.append("/".join(fdn.split("FDN : ")[1].split(",")))
        return existing_fdn_list

    def prepare_data(self, user, nodes, req_counts, number_of_threads):  # pylint: disable=W0223
        """
        This is a dummy method for prepare_data that must be overridden in the derived class.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :param req_counts: Number of requests for various types of requests depending on the size of the network
        :type req_counts: dict
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :return: MO data in the format required for threads to be executed
        :raises NotImplementedError: If method is not overridden by derived class
        """
        raise NotImplementedError("This is a dummy method for prepare_data that must be "
                                  "overridden in the derived class.")

    def configure_mo_data(self, req, user, nodes):  # pylint: disable=W0223
        """
        This is a dummy method for configure_mo_data that must be overridden in the derived class.

        :param req: Identifier for the request type
        :type req: str
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :raises NotImplementedError: If method is not overridden by derived class
        """
        raise NotImplementedError("This is a dummy method for configure_mo_data that must be "
                                  "overridden in the derived class.")

    def prepare_data_for_req(self, req, user, nodes, req_counts, number_of_threads, randomize_mo_data=True):
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
        :param number_of_threads: number of threads of profile
        :type number_of_threads: int
        :param randomize_mo_data: Whether to randomize MO data and repeat it so that the required
                                  number of requests are met
        :type randomize_mo_data: bool
        :return: Required data for a specific type of request
        :rtype: list
        """
        log.logger.debug("Starting attempt to prepare the required data for - {0}.".format(req))
        mo_data = self.configure_mo_data(req, user, nodes)
        mo_chunk_size_list = []
        for i in range(number_of_threads):
            mo_chunk_size_list.append(req_counts[req] / number_of_threads)
        for i in range(req_counts[req] % number_of_threads):
            mo_chunk_size_list[i] = req_counts[req] / number_of_threads + 1
        if not mo_data or not mo_chunk_size_list:
            log.logger.debug("Unable to form data for {0} in this iteration. "
                             "Required nodes/MOs may not be present in the deployment.".format(req))
            return []
        if randomize_mo_data:
            mos_for_workers = sum([[(req, random.choice(mo_data.values()))] * i for i in mo_chunk_size_list], [])
        else:
            mos_for_workers = [mo_data[i] for i in mo_data]
        log.logger.debug("Completed attempt to prepare the required data for - {0}.".format(req))
        return mos_for_workers

    @staticmethod
    def get_random_mo_data(response, list_of_fdns):
        """
        Get list of FDNs matching the cmedit command and randomly select a FDN for each node.

        :param response: Response of command sent to be executed on ENM scripting
        :type response: `terminal.TerminalOutput`
        :param list_of_fdns:List of FDNs
        :type list_of_fdns: list
        :return: FDN of a random MO from the response
        :rtype: str
        :raises EnvironWarning: Unable to get list of FDNs
        """
        for line in response.get_output():
            if "FDN" in line:
                list_of_fdns.append(line)
        if not list_of_fdns:
            raise EnvironWarning("Unable to get a get list of FDNs matching given criteria."
                                 "Issue could be either with environment or response of cmedit "
                                 "command sent to this function.")
        random_fdn = random.choice(list_of_fdns)
        random_fdn = "/".join(random_fdn.split("FDN : ")[1].split(","))
        return random_fdn

    def get_mo_data_req_based_on_cell_type(self, user, nodes):
        """
        Generate data through cmedit commands based on cell type.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :return: MO data
        :rtype: dict
        """
        log.logger.debug("Starting attempt to generate data through cmedit commands based on cell type.")
        mo_data = {}
        for node in nodes:
            list_of_fdns = []
            node_id = node.node_id
            try:
                if node.lte_cell_type == "TDD":
                    response = user.enm_execute(CMEDIT_GET_CELL_CMD.format(node_id, REQ_1_2_3_CELLS_CMD[0]))
                elif node.lte_cell_type == "FDD":
                    response = user.enm_execute(CMEDIT_GET_CELL_CMD.format(node_id, REQ_1_2_3_CELLS_CMD[1]))
                else:
                    response = user.enm_execute(CMEDIT_GET_CELL_CMD.format(node_id, REQ_1_2_3_CELLS_CMD[2]))
                mo_data[node_id] = self.get_random_mo_data(response, list_of_fdns)
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.debug("Completed attempt to generate data through cmedit commands based on cell type.")
        return mo_data

    @staticmethod
    def get_final_path_for_url(req, mo_path):  # pylint: disable=W0223
        """
        This is a dummy method for get_final_path_for_url that must be overridden in the derived class.

        :param req: Identifier for the request type
        :type req: str
        :param mo_path: MO path
        :type mo_path: str
        :raises NotImplementedError: If method is not overridden by derived class
        """
        raise NotImplementedError("This is a dummy method for get_final_path_for_url that must be "
                                  "overridden in the derived class.")

    @staticmethod
    def task_set(worker, profile, user):  # pylint: disable=arguments-differ
        """
        Method to make the REST request

        :param worker: tuple of request type and path of MO on which request is executed
        :type worker: tuple
        :param profile: limit for each user consuming events
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        """
        req, mo_path = worker
        final_path_for_url = profile.get_final_path_for_url(req, mo_path)
        profile.get_given_url(user, final_path_for_url)
