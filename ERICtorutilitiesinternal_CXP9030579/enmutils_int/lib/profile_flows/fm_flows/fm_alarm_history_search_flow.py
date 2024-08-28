from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.fm import create_empty_workspaces_for_given_users, HISTORICAL
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import execute_alarm_search_tasks, ALARM_SEARCH


class FmAlarmHistorySearchFlow(GenericFlow):
    """
    Class for Alarm History functions that need access to the profile object in Alarm History profiles
    """

    def execute_flow_fm_alarm_history_search(self):
        """
        This function executes the main flow for FM alarm history search
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes = self.get_nodes_list_by_attribute()
        self.state = "RUNNING"
        try:
            search_user_dict = create_empty_workspaces_for_given_users(users, ALARM_SEARCH)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Creation of Alarm Search workspaces failed "
                                                            "Msg: {}".format(e)))
        else:
            node_data = {"managedElements": [node.node_id for node in nodes], "actionType": "",
                         "uId": ""}
            while self.keep_running():
                self.sleep_until_next_scheduled_iteration()
                self.create_and_execute_threads(workers=users, thread_count=len(users),
                                                func_ref=execute_alarm_search_tasks,
                                                args=[node_data, search_user_dict, nodes,
                                                      HISTORICAL, self.TIME_SPAN], join=60,
                                                wait=60 * 15)
