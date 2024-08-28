#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from enmutils_int.lib.profile_flows.fm_flows.fm_10_flow import Fm10
from testslib import unit_test_utils


class Fm10UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [Mock(node_id='ieatnetsimv5051-01_LTE01ERBS00001'),
                      Mock(node_id='ieatnetsimv5051-01_LTE01ERBS00002')]
        self.flow = Fm10()
        self.flow.NUM_USERS = 2
        self.flow.USER_ROLES = "TEST1"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.execute_alarm_acknowledgement_tasks")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.create_empty_workspaces_for_given_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.create_profile_users")
    def test_execute_flow_fm_10__is_successful(self, mock_create_user, mock_create_empty_workspaces,
                                               mock_sleep_until_day, mock_alarm_ack, *_):
        mock_create_user.return_value = [self.user]
        self.flow.execute_flow_fm_10()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_create_empty_workspaces.call_count, 1)
        self.assertEqual(mock_sleep_until_day.call_count, 1)
        self.assertEqual(mock_alarm_ack.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.execute_alarm_acknowledgement_tasks")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.create_empty_workspaces_for_given_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.create_profile_users")
    def test_execute_flow_fm_10__continues_with_errors(self, mock_create_user, mock_create_empty_workspaces,
                                                       mock_add_exception, mock_alarm_ack, *_):
        mock_create_user.return_value = [self.user]
        mock_create_empty_workspaces.side_effect = Exception
        mock_alarm_ack.side_effect = Exception
        self.flow.execute_flow_fm_10()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_create_empty_workspaces.call_count, 1)
        self.assertEqual(mock_add_exception.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.acknowledge_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.log")
    def test_execute_alarm_acknowledgement_tasks__is_succesful(self, mock_log, *_):
        user_dict = {self.user.username: ('12345687', '4687459')}
        node_data = {"managedElements": [node.node_id for node in self.nodes], "actionType": "", "uId": ""}
        self.flow.execute_alarm_acknowledgement_tasks(self.user, self.nodes, user_dict, node_data)
        self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.acknowledge_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.log")
    def test_execute_alarm_acknowledgement_tasks__empty_user_dictionary(self, mock_log, *_):
        user_dict = {}
        node_data = {"managedElements": [node.node_id for node in self.nodes], "actionType": "", "uId": ""}
        self.flow.execute_alarm_acknowledgement_tasks(self.user, self.nodes, user_dict, node_data)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.delete_nodes_from_a_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.acknowledge_alarms")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.add_nodes_to_given_workspace_for_a_user")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.log")
    def test_execute_alarm_acknowledgement_tasks__is_failed(self, mock_log, *_):
        user_dict = {self.user.username: ('12345687', None)}
        node_data = {"managedElements": [node.node_id for node in self.nodes], "actionType": "", "uId": ""}
        self.flow.execute_alarm_acknowledgement_tasks(self.user, self.nodes, user_dict, node_data)
        self.assertEqual(mock_log.logger.info.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
