from enmutils.lib import log
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.nhm_ui import nhm_widget_flows
from enmutils_int.lib.nhm_widget import NodesBreached
from enmutils_int.lib.profile_flows.nhm_flows.nhm_multi_node_flow import NhmMultiNodeFlow


class Nhm07(NhmMultiNodeFlow):

    def execute_flow(self):
        """
        Executes the flow of NHM_07 profile

        """
        users, nodes_verified_on_enm = self.setup()
        widgets = []
        user_widgets = []

        for user in users:
            nodes_breached_widget = NodesBreached(user=user, nodes=nodes_verified_on_enm, number_of_kpis=10, kpi_type=self.REPORTING_OBJECT)
            widgets.append(nodes_breached_widget)
            user_widgets.append([nodes_breached_widget])
            self.teardown_list.append(picklable_boundmethod(nodes_breached_widget.teardown))
        self.create_and_configure_widgets(widgets)
        self.state = "RUNNING"
        while self.keep_running():
            tq = ThreadQueue(user_widgets, num_workers=len(widgets), func_ref=nhm_widget_flows)
            tq.execute()
            num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
            log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more details"
                             .format(self.NAME, num_exceptions))

            self.sleep()
