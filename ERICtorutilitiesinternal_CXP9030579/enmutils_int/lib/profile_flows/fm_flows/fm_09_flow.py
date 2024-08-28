import time
from random import randint

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (execute_alarm_monitor_tasks, ALARM_VIEWER,
                                                                     put_profile_to_sleep)
from enmutils_int.lib.fm import (create_empty_workspaces_for_given_users, create_alarm_overview_dashboards,
                                 alarm_overview_home, network_explorer_search_for_nodes, alarm_overview)


class Fm09(GenericFlow):
    """
    Class for FM_09 Alarm Monitor functions that need access to the profile object
    """

    def execute_flow_fm_09(self):
        """
        This function executes the main flow for FM_09
        """
        monitor_user_dict = {}
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid"])
        self.state = "RUNNING"

        split_index = len(users) / 2
        alarm_monitor_users = users[:split_index]
        alarm_overview_users = users[split_index:]
        log.logger.debug("Starting creation of {0} alarm monitor workspaces and {1} alarm overview dashboards."
                         .format(len(alarm_overview_users), len(alarm_overview_users)))

        node_data = {"managedElements": [node.node_id for node in nodes], "actionType": "", "uId": ""}
        try:
            monitor_user_dict = create_empty_workspaces_for_given_users(alarm_monitor_users, ALARM_VIEWER)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Creation of Alarm Monitor workspaces failed "
                                                            "Msg: {0}".format(e)))

        try:
            create_alarm_overview_dashboards(alarm_overview_users, nodes)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Creation of Alarm Overview dashboard failed "
                                                            "Msg: {}".format(e)))
        while self.keep_running():
            if alarm_monitor_users:
                self.create_and_execute_threads(workers=alarm_monitor_users, thread_count=len(alarm_monitor_users),
                                                func_ref=execute_alarm_monitor_tasks,
                                                args=[node_data, monitor_user_dict, len(nodes)], join=60, wait=60 * 15)
            log.logger.info("Sleeping for {0} seconds before starting alarm overview "
                            "tasks".format(self.ALARM_MONITOR_SLEEP))
            time.sleep(self.ALARM_MONITOR_SLEEP)
            if alarm_overview_users:
                self.create_and_execute_threads(workers=alarm_overview_users, thread_count=len(alarm_overview_users),
                                                func_ref=self.execute_alarm_overview_tasks_user, join=60, wait=60 * 15)
            put_profile_to_sleep(self, self.SCHEDULE_SLEEP)

    @staticmethod
    def execute_alarm_overview_tasks_user(user):
        """
        Function to execute alarm overview tasks
        :param user: User to execute tasks
        :type user: `enmutils.lib.enm_user_2.User`
        """
        init_sleep = randint(1, 60)
        sleep_between_requests_time = 74
        log.logger.debug("Starting task set for user {0} in {1} seconds.".format(user.username, init_sleep))
        time.sleep(init_sleep)
        log.logger.debug("Making GET request to Alarm Overview home.")
        alarm_overview_home(user=user)
        log.logger.debug("Sleeping for {0} before making next request.".format(sleep_between_requests_time))
        time.sleep(sleep_between_requests_time)
        network_explorer_search_for_nodes(user=user)
        log.logger.debug("Sleeping for {0} before making next request.".format(sleep_between_requests_time))
        time.sleep(sleep_between_requests_time)
        log.logger.debug("Starting polling of Alarm Overview.")
        alarm_overview(user=user, sleep=500, heart_beat_refresh_time=sleep_between_requests_time)
        log.logger.debug("Completed polling of Alarm Overview.")
