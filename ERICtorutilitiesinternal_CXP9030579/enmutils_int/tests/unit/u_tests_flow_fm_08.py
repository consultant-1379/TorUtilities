#!/usr/bin/env python

import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.fm_flows.fm_08_flow import Fm08
from testslib import unit_test_utils


class Fm08UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = [Mock(username='Test_User_1'), Mock(username='Test_User_2')]
        self.nodes = [Mock(node_id='ieatnetsimv5051-01_LTE01ERBS00001'),
                      Mock(node_id='ieatnetsimv5051-01_LTE01ERBS00002')]
        self.flow = Fm08()
        self.flow.NUM_USERS = 2
        self.flow.NUM_USERS_1 = 1
        self.flow.NUM_USERS_2 = 1
        self.flow.ALARM_MONITOR_SLEEP = 1
        self.flow.USER_ROLES = "TEST1"
        self.flow.SCHEDULE_SLEEP = 2
        self.good_response = Mock(rc=0, stdout="'Plan Status: Successful'")
        self.error_response = [Exception("Some Exception")]
        self.time_span = 1
        self.search_type = 'OPEN'

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.create_empty_workspaces_for_given_users")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_profile_users')
    def test_execute_flow_fm_08__is_successful(self, mock_create_user, mock_get_nodes, mock_create_empty_workspace,
                                               mock_create_and_execute_threads, mock_log, *_):
        mock_create_user.return_value = [self.user]
        mock_get_nodes.return_value = self.nodes
        self.flow.execute_flow_fm_08()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_create_and_execute_threads.call_count, 2)
        self.assertEqual(mock_get_nodes.call_count, 1)
        self.assertTrue(mock_log.logger.info.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.time")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_and_execute_threads')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.create_empty_workspaces_for_given_users")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_profile_users')
    def test_execute_flow_fm_08__does_not_execute_tasks_if_no_users_were_created(self, mock_create_user, mock_get_nodes,
                                                                                 mock_create_empty_workspace,
                                                                                 mock_create_and_execute_threads,
                                                                                 mock_log, *_):
        mock_create_user.return_value = []
        mock_get_nodes.return_value = self.nodes
        self.flow.execute_flow_fm_08()
        self.assertEqual(mock_create_user.call_count, 1)
        self.assertEqual(mock_get_nodes.call_count, 1)
        self.assertFalse(mock_log.logger.info.called)
        self.assertFalse(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.time')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.create_empty_workspaces_for_given_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.add_error_as_exception')
    def test_execute_flow_fm_08__continues_with_errors(self, mock_add_error, mock_get_nodes, mock_create_empty_workspace,
                                                       mock_create_and_execute_threads, mock_create_users, *_):
        mock_create_empty_workspace.side_effect = [Exception, Exception]
        mock_create_users.return_value = [self.user]
        mock_get_nodes.return_value = self.nodes
        self.flow.execute_flow_fm_08()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_get_nodes.call_count, 1)
        self.assertEqual(mock_create_and_execute_threads.call_count, 2)
        self.assertEqual(mock_add_error.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.time')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.log')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.create_empty_workspaces_for_given_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.add_error_as_exception')
    def test_execute_flow_fm_08__execute_tasks_with_errors(self, mock_add_error, mock_get_nodes,
                                                           mock_create_empty_workspace,
                                                           mock_create_and_execute_threads, mock_create_users, *_):
        mock_create_and_execute_threads.side_effect = [Exception, Exception]
        mock_create_users.return_value = [self.user]
        mock_get_nodes.return_value = self.nodes
        self.flow.execute_flow_fm_08()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_get_nodes.call_count, 1)
        self.assertEqual(mock_create_empty_workspace.call_count, 2)
        self.assertEqual(mock_add_error.call_count, 2)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
