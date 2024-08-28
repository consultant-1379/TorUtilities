import random

from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.nhm_ui import create_widgets_taskset, nhm_widget_flows
from enmutils_int.lib.nhm_widget import NodesBreached, MostProblematic, NetworkOperationalState, NetworkSyncStatus
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile


class Nhm11(NhmFlowProfile):

    WIDGETS = ["NodesBreached", "MostProblematic", "NetworkOperationalState", "NetworkSyncStatus"]

    def create_widget_objects(self, users, number_of_kpis, nodes):
        """
        Creates the widgets to be used in the UI flow

        :param users: users who will monitor using widgets
        :type users: list
        :param nodes: List of nodes to add to the widget
        :type  nodes: list
        :param number_of_kpis: Number of kpis to be used in the widget
        :type number_of_kpis: int
        :return: List of widgets created
        :rtype: list

        """
        widgets = list()
        for user in users:
            widget = random.choice(self.WIDGETS)
            holder = list()
            if widget == "NodesBreached":
                holder.append(NodesBreached(user=user, nodes=nodes, number_of_kpis=number_of_kpis))
            elif widget == "MostProblematic":
                holder.append(MostProblematic(user=user, nodes=nodes))
            elif widget == "NetworkOperationalState":
                holder.append(NetworkOperationalState(user=user, nodes=nodes))
            else:
                holder.append(NetworkSyncStatus(user=user, nodes=nodes))
            widgets.append(holder)

        return widgets

    def execute_flow(self):
        """
        Executes the flow of NHM_11 profile

        """

        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()

        widgets = self.create_widget_objects(operator_users, self.NUMBER_OF_KPIS, nodes_verified_on_enm)

        # Build teardown list
        for widget_list in widgets:
            for widget in widget_list:
                self.teardown_list.append(picklable_boundmethod(widget.teardown))

        self.state = "RUNNING"
        tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=create_widgets_taskset)
        tq.execute()

        self.process_thread_queue_errors(tq)

        while self.keep_running():
            if widgets:
                tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=nhm_widget_flows, args=[1])
                tq.execute()
                self.process_thread_queue_errors(tq)

            self.sleep()
