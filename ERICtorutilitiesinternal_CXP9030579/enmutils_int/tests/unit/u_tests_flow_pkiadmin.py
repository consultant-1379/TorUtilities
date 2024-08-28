#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils

from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow import PkiAdmin01Flow, execute_pkiadmin_commands
from enmutils_int.lib.workload import pkiadmin_01


class PkiAdmin01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.pki_commands = ["pkiadm entitymgmt --list --entitytype ca", "pkiadm entitymgmt --list --entitytype ee"]
        unit_test_utils.setup()
        self.pkiadmin_01 = pkiadmin_01.PKIADMIN_01()
        self.flow = PkiAdmin01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["ADMINISTRATOR"]
        self.flow.SCHEDULE_SLEEP = 60

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.execute_flow')
    def test_run__in_pkiadmin_01_is_successful(self, _):
        self.pkiadmin_01.run()

    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.execute_pkiadmin_commands")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.multitasking."
           "create_single_process_and_execute_task")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.create_profile_users")
    def test_execute_flow__is_successful(self, mock_create_users, mock_keep_running, mock_add_error, mock_sleep,
                                         mock_create_single_process_and_execute_task, *_):
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertTrue(mock_create_single_process_and_execute_task.called)
        self.assertTrue(mock_create_users.called)
        self.assertFalse(mock_add_error.called)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.execute_pkiadmin_commands")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.multitasking."
           "create_single_process_and_execute_task")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.sleep")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.keep_running")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.create_profile_users")
    def test_execute_flow__raises_env_error_while_calling_execute_pkiadmin_commands(
            self, mock_create_users, mock_keep_running, mock_add_error, mock_sleep,
            mock_create_single_process_and_execute_task, *_):
        mock_create_users.return_value = [self.user]
        mock_keep_running.side_effect = [True, False]
        mock_create_single_process_and_execute_task.side_effect = EnvironError("Something is wrong")
        self.flow.execute_flow()
        self.assertTrue(mock_create_single_process_and_execute_task.called)
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertTrue(call(mock_create_single_process_and_execute_task.side_effect in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.add_error_as_exception")
    def test_execute_pkiadmin_commands__if_pkiadmin_commands_executed_successfully(self, mock_add_error,
                                                                                   mock_log_debug,
                                                                                   mock_check_profile_memory_usage):
        self.flow.user = self.user
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = ["Command Executed Successfully"]
        execute_pkiadmin_commands(self.flow)
        self.assertTrue(mock_log_debug.call_count, 2)
        self.assertTrue(mock_check_profile_memory_usage.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow.PkiAdmin01Flow.add_error_as_exception")
    def test_execute_pkiadmin_commands__raises_env_error(self, mock_add_error, mock_log_debug,
                                                         mock_check_profile_memory_usage):
        self.flow.user = self.user
        self.flow.user.enm_execute.side_effect = Exception("something is wrong")
        execute_pkiadmin_commands(self.flow)
        self.assertTrue(mock_log_debug.call_count, 2)
        message = EnvironError("2 pki admin commands execution was failed")
        self.assertTrue(call(message in mock_add_error.mock_calls))
        self.assertTrue(mock_check_profile_memory_usage.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
