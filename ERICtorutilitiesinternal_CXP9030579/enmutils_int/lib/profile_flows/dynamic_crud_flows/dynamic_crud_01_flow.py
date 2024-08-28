from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.dynamic_crud import (SINGLE_MO_ALL_CHILD_URL, SINGLE_MO_WITH_ATTR_URL,
                                           SINGLE_NODE_ALL_ATTRIBUTES_WITH_MO_TYPE_URL)
from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_flow import DynamicCrudFlow

REQ_4_5_6_ATTRS = ["cellRange,administrativeState,eutranCellPolygon",
                   "administrativeState,ssacBarringForMMTELVideo,arpPriorityLevelForSPIFHo",
                   "administrativeState,csiRsConfig2P&fields=attributes/csiRsConfig4P/csiRsControl4Ports"]
REQ_7_to_10_ATTRS = {"REQ_7": "EUtranFreqRelation", "REQ_8": "NRFreqRelation", "REQ_9": "ENodeBFunction",
                     "REQ_10": "GNBCUCPFunction"}


class DynamicCrud01Flow(DynamicCrudFlow):
    """
    Class for flow of DYNAMIC_CRUD_01.
    """
    NUMBER_OF_THREADS = 3

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
        self.mo_data_cells = {}
        self.mo_data_nodes_4g = {}
        self.mo_data_nodes_5g = {}
        mos_for_workers_req_1_2_3 = self.prepare_data_for_req("REQ_1_2_3", user, nodes,
                                                              req_counts, number_of_threads)
        mos_for_workers_req_4_5_6 = self.prepare_data_for_req("REQ_4_5_6", user, nodes,
                                                              req_counts, number_of_threads)
        nodes_4g = [node for node in nodes if "LTE" in node.node_id]
        mos_for_workers_req_7 = self.prepare_data_for_req("REQ_7", user, nodes_4g,
                                                          req_counts, number_of_threads)
        mos_for_workers_req_9 = self.prepare_data_for_req("REQ_9", user, nodes_4g,
                                                          req_counts, number_of_threads)
        nodes_5g = [node for node in nodes if "NR" in node.node_id]
        mos_for_workers_req_8 = self.prepare_data_for_req("REQ_8", user, nodes_5g,
                                                          req_counts, number_of_threads)
        mos_for_workers_req_10 = self.prepare_data_for_req("REQ_10", user, nodes_5g,
                                                           req_counts, number_of_threads)
        mos_for_workers = (mos_for_workers_req_1_2_3 + mos_for_workers_req_4_5_6 + mos_for_workers_req_7 +
                           mos_for_workers_req_8 + mos_for_workers_req_9 + mos_for_workers_req_10)
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
        if self.mo_data_cells and (req == "REQ_1_2_3" or req == "REQ_4_5_6"):
            mo_data = self.mo_data_cells
        elif self.mo_data_nodes_4g and (req == "REQ_7" or req == "REQ_9"):
            mo_data = self.mo_data_nodes_4g
        elif self.mo_data_nodes_5g and (req == "REQ_8" or req == "REQ_10"):
            mo_data = self.mo_data_nodes_5g
        else:
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
        if req == "REQ_1_2_3" or req == "REQ_4_5_6":
            self.mo_data_cells = self.get_mo_data_req_based_on_cell_type(user, nodes)
            mo_data = self.mo_data_cells
        elif req == "REQ_7" or req == "REQ_9":
            self.mo_data_nodes_4g = self.get_mo_data_req_7_to_10(user, nodes)
            mo_data = self.mo_data_nodes_4g
        elif req == "REQ_8" or req == "REQ_10":
            self.mo_data_nodes_5g = self.get_mo_data_req_7_to_10(user, nodes)
            mo_data = self.mo_data_nodes_5g
        log.logger.debug("Completed attempt to generate data through cmedit commands for - {0}.".format(req))
        return mo_data

    def get_mo_data_req_7_to_10(self, user, nodes):
        """
        Generate data through cmedit commands for any request type from 7 to 10.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param nodes: List of nodes
        :type nodes: list
        :return: MO data
        :rtype: dict
        """
        log.logger.debug("Starting attempt to generate data through cmedit commands for any request type from 7 to 10.")
        mo_data = {}
        for node in nodes:
            list_of_fdns = []
            node_id = node.node_id
            try:
                response = user.enm_execute("cmedit get {0}".format(node_id))
                mo_data[node_id] = self.get_random_mo_data(response, list_of_fdns)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
        log.logger.debug("Completed attempt to generate data through cmedit commands for any request type from 7 to 10.")
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
        final_path_for_url = ""
        if req == "REQ_1_2_3":
            base_url_for_mo = SINGLE_MO_ALL_CHILD_URL
            final_path_for_url = base_url_for_mo.format(mo_path)
        elif req == "REQ_4_5_6":
            base_url_for_mo = SINGLE_MO_WITH_ATTR_URL
            if "FDD" in mo_path:
                attrs = REQ_4_5_6_ATTRS[0]
            elif "TDD" in mo_path:
                attrs = REQ_4_5_6_ATTRS[1]
            else:
                attrs = REQ_4_5_6_ATTRS[2]
            final_path_for_url = base_url_for_mo.format(mo_path, attrs)
        elif req == "REQ_7" or req == "REQ_8" or req == "REQ_9" or req == "REQ_10":
            base_url_for_mo = SINGLE_NODE_ALL_ATTRIBUTES_WITH_MO_TYPE_URL
            final_path_for_url = base_url_for_mo.format(mo_path, REQ_7_to_10_ATTRS[req])
        return final_path_for_url

    def remove_existing_mo(self, user, existing_mo_list):  # pylint: disable=W0223
        """
        Method to remove the existing MOs.

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param existing_mo_list: List of existing MO
        :type existing_mo_list: list
        """
        pass
