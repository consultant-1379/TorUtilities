import time
from random import randint

from enmutils.lib import log
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.nhm import sleep_until_profile_persisted, wait_for_nhm_setup_profile, SETUP_PROFILE
from enmutils_int.lib.nhm_ui import nhm_landing_page_flow, nhm_widget_flows
from enmutils_int.lib.nhm_widget import NhmWidget, MostProblematic, CellStatus
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


def taskset(widgets, profile):
    """
    UI Flow to be used to run this profile

    :param widgets: widgets on which to perform actions
    :type widgets: enmutils_int.lib.nhm_widget.NhmWidget
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`

    """
    for widget in widgets:
        try:
            nhm_landing_page_flow(user=widget.user)
            nhm_widget_flows([widget])
        except Exception as e:
            profile.add_error_as_exception(e)


def create_widgets_taskset(widgets, profile):
    """
    Create the widgets to be used in the UI flow

    :param widgets: widgets on which to perform actions
    :type widgets: enmutils_int.lib.nhm_widget.NhmWidget
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`

    """
    time.sleep(randint(0, 60))
    for widget in widgets:
        try:
            widget.create()
        except Exception as e:
            profile.add_error_as_exception(e)
        time.sleep(5)


class Nhm08(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow of NHM_08 profile

        """
        sleep_until_profile_persisted(SETUP_PROFILE)
        wait_for_nhm_setup_profile()
        admin_users = self.create_users(self.NUM_ADMINS, self.ADMIN_ROLE, fail_fast=False, safe_request=True, retry=True)
        operator_users = self.create_users(self.NUM_OPERATORS, self.OPERATOR_ROLE, fail_fast=False, safe_request=True, retry=True)
        users = admin_users + operator_users
        nodes_verified_on_enm = self.get_allocated_nodes(SETUP_PROFILE)
        if len(nodes_verified_on_enm) > self.TOTAL_NODES:
            nodes_verified_on_enm = nodes_verified_on_enm[:self.TOTAL_NODES]

        widgets = []
        cell_widgets = []

        for user in users:
            widgets_init = []
            widgets_init.append(MostProblematic(user=user, nodes=nodes_verified_on_enm))
            for _ in xrange(self.NUM_USERS):
                widgets_init.append(CellStatus(user=user, nodes=nodes_verified_on_enm))

            cell_widgets.append(widgets_init[-1:])
            widgets.append(widgets_init)

        for widget_list in widgets:
            for widget in widget_list:
                self.teardown_list.append(widget)

        self.state = "RUNNING"
        tq = ThreadQueue(widgets, num_workers=len(users), func_ref=create_widgets_taskset, args=[self])

        number_widgets = 0
        while number_widgets == 0:
            tq.execute()
            num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
            log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more details"
                             .format(self.NAME, num_exceptions))
            number_widgets = sum([NhmWidget.number_created_configured_widgets(widget) for widget in widgets])
            if number_widgets == 0:
                log.logger.debug("Profile could not create widgets, Retrying in 30m")
                time.sleep(60 * 30)

        self.process_thread_queue_errors(tq)

        while self.keep_running():
            tq = ThreadQueue(cell_widgets, num_workers=len(users), func_ref=taskset, args=[self])
            tq.execute()
            num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
            log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more details"
                             .format(self.NAME, num_exceptions))
            self.sleep()
