#!/usr/bin/env python

import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow import FmAlarmHistorySearchFlow
from testslib import unit_test_utils


class FmAlarmHistorySearchUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes = []
        self.flow = FmAlarmHistorySearchFlow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = "TEST1"
        self.flow.TIME_SPAN = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'create_empty_workspaces_for_given_users')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.HISTORICAL')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.execute_alarm_search_tasks')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.keep_running')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.create_profile_users')
    def test_execute_flow_alarm_history_search_success(self, mock_create_user, mock_keep_running,
                                                       mock_sleep_until_next_scheduled_iteration, mock_create_and_execute_threads, *_):
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow_fm_alarm_history_search()
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_sleep_until_next_scheduled_iteration.called)
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'create_empty_workspaces_for_given_users', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.HISTORICAL')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.execute_alarm_search_tasks')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.keep_running')
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.'
           'FmAlarmHistorySearchFlow.create_profile_users')
    def test_execute_flow_alarm_history_search_raises_exception(self, mock_create_user, mock_keep_running,
                                                                mock_sleep_until_next_scheduled_iteration, mock_create_and_execute_threads,
                                                                mock_add_error_as_exception, *_):
        mock_create_user.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow_fm_alarm_history_search()
        self.assertTrue(mock_create_user.called)
        self.assertFalse(mock_keep_running.called)
        self.assertFalse(mock_sleep_until_next_scheduled_iteration.called)
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
