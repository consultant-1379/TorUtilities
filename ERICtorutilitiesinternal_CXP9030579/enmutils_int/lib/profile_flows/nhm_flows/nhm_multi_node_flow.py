from random import randint

from enmutils.lib import log
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.nhm_widget import CellStatus
from enmutils_int.lib.nhm_ui import call_widget_flow
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile


class NhmMultiNodeFlow(NhmFlowProfile):

    @staticmethod
    def taskset(widget):
        """
        UI Flow to be used to run this profile

        :param widget: Widget on which to perform actions
        :type widget: enmutils_int.lib.nhm_widget.NhmWidget

        """
        if isinstance(widget, CellStatus):
            # assign random poid on a widget
            widget.poid = widget.node_poids.values()[randint(1, len(widget.node_poids) - 1)]
            # map widget poid to ne_type an it is store on a widget
            widget.ne_type = widget.node_ne_types[widget.poid]
        else:
            log.logger.debug("No need to assign a poid to widget because it is not a CellStatus Widget")
        call_widget_flow(widget)

    def setup(self):
        """
        Setup the NHM profile. Wait for NHM_SETUP to complete, create users, and get nodes for NHM use.

        :return user: users of the profile
        :rtype user: enmutils.lib.enm_user_2.User
        :return nodes_verified_on_enm: list of nodes with correct POIDs to use for NHM
        :rtype nodes_verified_on_enm: list
        """

        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()
        admin_users = self.create_users(self.NUM_ADMINS, self.ADMIN_ROLE, fail_fast=False, safe_request=True, retry=True)
        users = admin_users + operator_users

        return users, nodes_verified_on_enm

    def execute_multi_node_flow(self, widgets):
        """
        Execute the common flow of nhm_05 and nhm_06

        :param widgets: list of widgets to use in the profile
        :type widgets: list
        """

        self.state = "RUNNING"
        while self.keep_running():
            tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=self.taskset)
            tq.execute()
            num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
            log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more details"
                             .format(self.NAME, num_exceptions))
            self.sleep()
