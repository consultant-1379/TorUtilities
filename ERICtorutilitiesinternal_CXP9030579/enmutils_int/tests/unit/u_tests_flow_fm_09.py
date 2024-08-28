#!/usr/bin/env python

import unittest2
from mock import patch, Mock
from requests.exceptions import HTTPError

from enmutils.lib.enm_node import ERBSNode
from enmutils_int.lib.profile_flows.fm_flows.fm_09_flow import Fm09
from testslib import unit_test_utils


class Fm09UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', '10.154.0.2', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', '10.154.0.3', 'F.1.101', '5783-904-386', '', 'netsim',
                     'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.flow = Fm09()
        self.flow.ALARM_MONITOR_SLEEP = 1
        self.flow.NUM_USERS = 2
        self.flow.USER_ROLES = "TEST1"
        self.flow.SCHEDULE_SLEEP = 2
        self.good_response = Mock(rc=0, stdout="'Plan Status: Successful'")
        self.error_response = [Exception("Some Exception")]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.time")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.create_empty_workspaces_for_given_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.create_alarm_overview_dashboards')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.keep_running')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.create_users')
    def test_execute_flow_fm_09__success(self, mock_create_users, mock_keep_running, mock_create_dashboard,
                                         mock_create_empty_workspaces, mock_create_and_execute_threads, *_):
        mock_user = Mock()
        mock_create_users.return_value = [mock_user] * 2
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow_fm_09()

        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_create_dashboard.called)
        self.assertTrue(mock_create_empty_workspaces.called)
        self.assertEqual(mock_create_and_execute_threads.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.time")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.create_empty_workspaces_for_given_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.create_alarm_overview_dashboards')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.create_users', return_value=[])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.create_and_execute_threads')
    def test_execute_flow_fm_09__success_no_users(self, mock_create_and_execute_threads, *_):
        self.flow.execute_flow_fm_09()

        self.assertEqual(mock_create_and_execute_threads.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.time")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.put_profile_to_sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.create_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.create_empty_workspaces_for_given_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.create_alarm_overview_dashboards')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.keep_running')
    def test_execute_flow_fm_09__throws_errors(
            self, mock_keep_running, mock_create_dashboard, mock_create_empty_workspaces,
            mock_create_and_execute_threads, mock_add_error_as_exception, *_):
        mock_create_empty_workspaces.side_effect = HTTPError()
        mock_create_dashboard.side_effect = HTTPError()
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow_fm_09()

        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_create_dashboard.called)
        self.assertTrue(mock_create_empty_workspaces.called)
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.alarm_overview')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.network_explorer_search_for_nodes')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.alarm_overview_home')
    def test_execute_alarm_overview_tasks_user(self, mock_alarm_overview_home, mock_search_for_node,
                                               mock_alarm_overview, mock_sleep):
        mock_user = Mock()
        self.flow.execute_alarm_overview_tasks_user(mock_user)

        self.assertTrue(mock_alarm_overview.called)
        self.assertTrue(mock_alarm_overview_home.called)
        self.assertTrue(mock_search_for_node.called)
        self.assertTrue(mock_sleep.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
