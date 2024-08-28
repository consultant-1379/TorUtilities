from enmutils.lib import log
from enmutils_int.lib.load_node import filter_nodes_having_poid_set
from enmutils_int.lib.nhm import NhmKpi, CREATED_BY_DEFAULT
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Nhm13Flow(GenericFlow):

    def activate_kpi(self, user, kpi_list, selected_nodes):
        """
        Create and activate predefined cell level KPIs
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param kpi_list: List with predefined KPIs that are needed to be used
        :type kpi_list: List
        :param selected_nodes: List of nodes to be assigned to the KPI
        :type selected_nodes: List
        """
        log.logger.debug("Executing for user {0}".format(user.username))
        usable_kpis = kpi_list
        try:
            po_ids = [node.poid for node in filter_nodes_having_poid_set(selected_nodes)]
            for kpi_name in usable_kpis:
                kwargs = {"name": kpi_name, "nodes": selected_nodes, "user": user, "po_ids": po_ids,
                          "created_by": CREATED_BY_DEFAULT}
                default_kpi = NhmKpi(**kwargs)
                default_kpi.activate()
        except Exception as e:
            self.add_error_as_exception(e)

    def expected_count(self, used_nodes):
        """
        Gives the expected count of the KPIs
        :param used_nodes: Nodes used by the profile
        :type used_nodes: list
        """
        total_number_of_cells = len(used_nodes) * self.NUMBER_OF_CELLS
        log.logger.info(
            'Expected total number of KPI count: {}'.format(total_number_of_cells * self.NUMBER_OF_KPIS))

    def nodes_to_be_used(self, used_nodes, users):
        """
        Nodes to be assigned to the KPI per user
        :param used_nodes: Nodes used by the profile
        :type used_nodes: list
        :param users: Users for the profile
        :type users: list
        """
        offset_nodes = 0
        num_nodes = 20
        log.logger.debug("Proceeding with the available three cell nodes")
        for user in users:
            kpi_list = self.RECOMMENDED_KPIS
            remaining_nodes = len(used_nodes) - offset_nodes
            if remaining_nodes:
                nodes = used_nodes[offset_nodes:offset_nodes + num_nodes]
                self.activate_kpi(user, kpi_list, nodes)
                offset_nodes += num_nodes if remaining_nodes >= num_nodes else remaining_nodes

    def execute_flow(self):
        """
        Executes the flow of NHM_13 profile
        """
        users = self.create_profile_users(self.NUM_OPERATORS, self.OPERATOR_ROLE)
        self.state = "RUNNING"
        while self.keep_running():
            try:
                three_cell_nodes = self.get_nodes_with_required_number_of_cells()
            except Exception as e:
                self.add_error_as_exception(e)
            else:
                used_nodes = three_cell_nodes[:self.REQUIRED_NODES]
                self.deallocate_unused_nodes_and_update_profile_persistence(used_nodes)
                self.nodes_to_be_used(used_nodes, users)
                self.expected_count(used_nodes)
                self.sleep()
                self.exchange_nodes()
