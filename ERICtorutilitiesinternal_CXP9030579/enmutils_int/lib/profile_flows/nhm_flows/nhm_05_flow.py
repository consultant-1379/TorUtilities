from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.nhm_widget import CellStatus, NetworkOperationalState
from enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow import NhmMultiNodeFlow


class Nhm05(NhmMultiNodeFlow):

    def _init_widgets(self, user, nodes):
        """
        It creates the NetworkOperationalState and CellStatus widgets for a user

        :param user: User object to be used to create the widgets
        :type user: enmutils.lib.enm_user_2.User
        :param nodes: List of nodes to add to the widget
        :type nodes: list

        :return: List of widgets created
        :rtype: list
        """

        widgets = []

        network_operational_state_widget = NetworkOperationalState(user=user, nodes=nodes)
        widgets.append(network_operational_state_widget)
        self.teardown_list.append(picklable_boundmethod(network_operational_state_widget.teardown))

        cell_status_widget = CellStatus(user=user, nodes=nodes, kpi_type=self.REPORTING_OBJECT, kpi_present=False)
        widgets.append(cell_status_widget)
        self.teardown_list.append(picklable_boundmethod(cell_status_widget.teardown))

        return widgets

    def execute_flow(self):
        """
        Executes the flow of NHM_05 profile
        """

        users, nodes_verified_on_enm = self.setup()

        widgets = []
        for user in users:
            widgets += self._init_widgets(user, nodes_verified_on_enm)

        self.create_and_configure_widgets(widgets)
        self.execute_multi_node_flow(widgets)
