import random
import time

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.nhm import sleep_until_profile_persisted, wait_for_nhm_setup_profile, SETUP_PROFILE
from enmutils_int.lib.nhm_widget import NhmWidget
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class NhmFlowProfile(GenericFlow):

    @staticmethod
    def create_widgets_taskset(widget):
        """
        Create the widgets to be used in the UI flow

        :param widget: Widget on which to perform actions
        :type widget: enmutils_int.lib.nhm_widget.NhmWidget

        """
        time.sleep(random.randint(0, 300))
        widget.create()

    def create_and_configure_widgets(self, widgets):
        """
        Create and configure the widgets to use in the profile flow

        :param widgets: list of widgets to create and configure
        :type widgets: list
        """

        tq = ThreadQueue(widgets, num_workers=len(widgets), func_ref=self.create_widgets_taskset)
        number_widgets = 0
        attempts = 0
        while number_widgets == 0:
            if attempts < 3:
                tq.execute()
                num_exceptions = self.process_thread_queue_errors(tq, last_error_only=True)
                log.logger.debug("{0} has encountered {1} thread queue exceptions. Please see log errors for more "
                                 "details".format(self.NAME, num_exceptions))
                number_widgets = NhmWidget.number_created_configured_widgets(widgets)
                if number_widgets == 0:
                    attempts += 1
                    log.logger.debug("Profile could not create and configure widgets, retrying in 5 minutes")
                    time.sleep(60 * 5)

            else:
                attempts = 0
                self.add_error_as_exception(EnvironError("Profile {0} has not been able to create and configure "
                                                         "widgets, retrying on next iteration".format(self.NAME)))
                log.logger.debug("Please ensure {0} profile has run successfully and that the kpiserv is "
                                 "online. Profile will attempt to run again on its next "
                                 "iteration".format(SETUP_PROFILE))
                self.sleep()

    def setup_nhm_profile(self):
        """
        Setup the NHM profile. Wait for the SETUP_PROFILE to complete, create users, and get nodes for NHM use.

        :return operator_users: operator_users of the profile
        :rtype operator_users: list
        :return nodes_verified_on_enm: list of nodes with correct POIDs to use for NHM
        :rtype nodes_verified_on_enm: list
        """
        sleep_until_profile_persisted(SETUP_PROFILE)
        wait_for_nhm_setup_profile()
        operator_users = self.create_users(self.NUM_OPERATORS, self.OPERATOR_ROLE, fail_fast=False, safe_request=True, retry=True)
        nodes_verified_on_enm = self.get_allocated_nodes(SETUP_PROFILE)
        if len(nodes_verified_on_enm) > self.TOTAL_NODES:
            nodes_verified_on_enm = nodes_verified_on_enm[:self.TOTAL_NODES]
        return operator_users, nodes_verified_on_enm
