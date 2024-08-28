#!/usr/bin/env python
import unittest2
from mock import patch, PropertyMock

from enmutils_int.lib.status_profile import StatusProfile
from testslib import unit_test_utils


class StatusProfileUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.status_profile.StatusProfile.running', new_callable=PropertyMock,
           return_value=False)
    @patch('enmutils_int.lib.status_profile.StatusProfile.does_process_name_match_with_profile_name',
           return_value=False)
    def test_status_profile__daemon_dies(self, mock_does_process_name_match_with_profile_name, _):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual(True, profile.daemon_died)
        self.assertTrue(mock_does_process_name_match_with_profile_name.called)

    @patch('enmutils_int.lib.status_profile.StatusProfile.running', new_callable=PropertyMock,
           return_value=True)
    @patch('enmutils_int.lib.status_profile.StatusProfile.does_process_name_match_with_profile_name',
           return_value=True)
    def test_status_profile__daemon_dies_if_profile_is_running(self, mock_does_process_name_match_with_profile_name, _):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual(False, profile.daemon_died)
        self.assertFalse(mock_does_process_name_match_with_profile_name.called)

    @patch('enmutils_int.lib.status_profile.StatusProfile.running', new_callable=PropertyMock,
           return_value=True)
    @patch('enmutils_int.lib.status_profile.StatusProfile.does_process_name_match_with_profile_name',
           return_value=False)
    def test_status_profile__daemon_dies_if_profile_name_and_process_name_is_not_matched(
            self, mock_does_process_name_match_with_profile_name, _):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual(False, profile.daemon_died)
        self.assertFalse(mock_does_process_name_match_with_profile_name.called)

    @patch('enmutils_int.lib.status_profile.persistence.get')
    def test_status_profile__errors_gets_profile_errors(self, mock_get):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        _ = profile.errors
        mock_get.assert_called_with("TEST_00-errors")

    @patch('enmutils_int.lib.status_profile.persistence.get')
    def test_status_profile__warnings_gets_profile_warnings(self, mock_get):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        _ = profile.warnings
        mock_get.assert_called_with("TEST_00-warnings")

    @patch('enmutils_int.lib.status_profile.process.is_pid_running', return_value=False)
    def test_status_profile__running(self, _):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual(False, profile.running)

    @patch('enmutils_int.lib.status_profile.process.is_pid_running', return_value=False)
    def test_status_profile__last_run_returns_last_run_if_available(self, _):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual("NEVER", profile.get_last_run_time())

    @patch('enmutils_int.lib.status_profile.process.is_pid_running', return_value=False)
    @patch('enmutils_int.lib.status_profile.StatusProfile.errors', new_callable=PropertyMock,
           side_effect=[False, True, False])
    @patch('enmutils_int.lib.status_profile.StatusProfile.warnings', new_callable=PropertyMock,
           side_effect=[True, False, False])
    @patch('enmutils_int.lib.status_profile.StatusProfile.daemon_died', new_callable=PropertyMock,
           side_effect=[True, False, False, False])
    def test_status_profile__status(self, *_):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual("DEAD", profile.status)
        self.assertEqual('WARNING', profile.status)
        self.assertEqual("ERROR", profile.status)
        self.assertEqual("OK", profile.status)

    def test_status_profile_run__pass(self):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        self.assertEqual(None, profile.run())

    @patch('enmutils_int.lib.status_profile.log.logger.debug')
    @patch('enmutils_int.lib.status_profile.process.get_process_name')
    def test_does_process_name_match_with_profile_name__if_profile_name_and_process_name_is_same(
            self, mock_get_process_name, mock_debug_log):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        mock_get_process_name.return_value = "TEST_00"
        self.assertEqual(True, profile.does_process_name_match_with_profile_name())
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch('enmutils_int.lib.status_profile.log.logger.debug')
    @patch('enmutils_int.lib.status_profile.process.get_process_name')
    def test_does_process_name_match_with_profile_name__if_profile_name_and_process_name_is_not_same(
            self, mock_get_process_name, mock_debug_log):
        request_data = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                        "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                        "user_count": 0}
        profile = StatusProfile(**request_data)
        mock_get_process_name.return_value = "TEST_01"
        self.assertEqual(False, profile.does_process_name_match_with_profile_name())
        self.assertEqual(mock_debug_log.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
