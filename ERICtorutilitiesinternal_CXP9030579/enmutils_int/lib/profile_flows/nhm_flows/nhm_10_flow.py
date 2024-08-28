from enmutils.lib import log
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.nhm_widget import NetworkOperationalState, NetworkSyncStatus
from enmutils_int.lib.nhm_ui import create_widgets_taskset, nhm_widget_flows
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile


class Nhm10(NhmFlowProfile):

    def create_widget_objects(self, users, nodes):
        """
        Creates the Network State Network Sync Status widgets to be used in the UI flow

        :param users: users who will monitor using widgets
        :type users: list
        :param nodes: List of nodes to add to the widget
        :type  nodes: list
        :return: List of widgets created
        :rtype: list

        """
        widgets = list()
        for user in users:
            state_widget = NetworkOperationalState(user=user, nodes=nodes)
            sync_widget = NetworkSyncStatus(user=user, nodes=nodes)
            self.teardown_list.append(picklable_boundmethod(state_widget.teardown))
            self.teardown_list.append(picklable_boundmethod(sync_widget.teardown))
            widgets.extend([[state_widget], [sync_widget]])

        return widgets

    def execute_flow(self):
        """
        Executes the flow of NHM_10 profile

        """
        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()

        widgets = self.create_widget_objects(operator_users, nodes_verified_on_enm)

        self.state = "RUNNING"
        tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=create_widgets_taskset)
        tq.execute()

        self.process_thread_queue_errors(tq)

        while self.keep_running():
            if widgets:
                tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=nhm_widget_flows)
                tq.execute()
                num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
                log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more "
                                 "details".format(self.NAME, num_exceptions))

            self.sleep()
