import time
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.fm import create_empty_workspaces_for_given_users, acknowledge_alarms
from enmutils_int.lib.profile_flows.fm_flows.fm_common_utils import (add_nodes_to_given_workspace_for_a_user,
                                                                     delete_nodes_from_a_given_workspace_for_a_user,
                                                                     ALARM_VIEWER)


class Fm10(GenericFlow):
    """
    Class for FM_10 Alarm acknowledgement functions that need access to the profile object
    """
    def execute_flow_fm_10(self):
        """
        This function executes the main flow for FM_10
        """
        monitor_user_dict = {}
        nodes = self.get_nodes_list_by_attribute()
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]

        self.state = "RUNNING"

        node_data = {"managedElements": [node.node_id for node in nodes], "actionType": "", "uId": ""}
        try:
            monitor_user_dict = create_empty_workspaces_for_given_users([user], ALARM_VIEWER)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Creation of Alarm Monitor workspaces failed "
                                                            "Msg: {}".format(e)))

        while self.keep_running():
            self.sleep_until_day()
            try:
                self.execute_alarm_acknowledgement_tasks(user, nodes, monitor_user_dict, node_data)
            except Exception as e:
                self.add_error_as_exception(e)

    @staticmethod
    def execute_alarm_acknowledgement_tasks(user, nodes, user_dict, node_data):
        """
        tasks to be performed for alarm acknowledgement
        :param user: User to execute tasks
        :type user: `enmutils.lib.enm_user_2.User`
        :param nodes: nodes which are allocated to the profile
        :type nodes: list
        :param user_dict: Dict containing username as key and workspace id, node group id as keys
        :type user_dict: dict
        :param node_data: Dict of nodes with action type and uid
        :type node_data: dict
        """
        if user.username in user_dict.keys():
            log.logger.info("Executing alarm ack tasks")
            workspace_id, node_group_id = user_dict.get(user.username)
            if workspace_id and node_group_id:
                node_data['actionType'] = 'Create'
                add_nodes_to_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, len(nodes), ALARM_VIEWER)
                time.sleep(60)
                acknowledge_alarms(user=user, nodes=nodes, num_alarms=1000)
                time.sleep(60)
                node_data['actionType'] = 'Delete'
                delete_nodes_from_a_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, ALARM_VIEWER)
        else:
            log.logger.debug("User {0} not found in user dictionary ".format(user.username))
