import time
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib import log
from enmutils_int.lib.fm import create_empty_workspaces_for_given_users
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (execute_alarm_monitor_tasks, ALARM_VIEWER,
                                                                     execute_alarm_search_tasks, ALARM_SEARCH,
                                                                     put_profile_to_sleep)


class Fm08(GenericFlow):
    """
    Class for FM_08 Alarm Monitor and Alarm Search functions that need access to the profile object.
    """
    def execute_flow_fm_08(self):
        """
        This function executes the main flow for FM_08
        """
        monitor_user_dict = search_user_dict = {}
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes = self.get_nodes_list_by_attribute()
        self.state = "RUNNING"
        alarm_monitor_users = users[:self.NUM_USERS_1]
        alarm_search_users = users[-self.NUM_USERS_2:]

        node_data = {"managedElements": [node.node_id for node in nodes], "actionType": "", "uId": ""}
        try:
            monitor_user_dict = create_empty_workspaces_for_given_users(alarm_monitor_users, ALARM_VIEWER)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Creation of Alarm Monitor workspaces failed "
                                                            "Msg: {0}".format(e)))

        try:
            search_user_dict = create_empty_workspaces_for_given_users(alarm_search_users, ALARM_SEARCH)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Creation of Alarm search workspaces failed "
                                                            "Msg: {0}".format(e)))

        while self.keep_running():
            try:
                if not alarm_monitor_users and monitor_user_dict:
                    raise EnvironError("Monitor User dictionary is empty to execute threads for Alarm Monitor Tasks")
                self.create_and_execute_threads(workers=alarm_monitor_users, thread_count=len(alarm_monitor_users),
                                                func_ref=execute_alarm_monitor_tasks,
                                                args=[node_data, monitor_user_dict, len(nodes)], join=60, wait=60 * 15)

                log.logger.info("Sleeping for {0} seconds before starting alarm search "
                                "tasks".format(self.ALARM_MONITOR_SLEEP))
                time.sleep(self.ALARM_MONITOR_SLEEP)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError("Unable to execute alarm monitor tasks Msg:{}".format(e)))

            try:
                if not alarm_search_users and search_user_dict:
                    raise EnvironError("Search user dictionary is empty to execute threads for Alarm Search Tasks")
                self.create_and_execute_threads(workers=alarm_search_users, thread_count=len(alarm_search_users),
                                                func_ref=execute_alarm_search_tasks,
                                                args=[node_data, search_user_dict, nodes], join=60,
                                                wait=60 * 15)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError("Unable to execute alarm search tasks Msg :{}".format(e)))
            put_profile_to_sleep(self, self.SCHEDULE_SLEEP)
