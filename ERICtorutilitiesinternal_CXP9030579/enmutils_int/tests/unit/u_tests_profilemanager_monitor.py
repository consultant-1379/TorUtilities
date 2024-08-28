#!/usr/bin/env python
from datetime import datetime
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase

import unittest2
from enmutils_int.lib.services import profilemanager_monitor
from testslib import unit_test_utils

TEST_PROFILE = "TEST_00"
WORKLOAD_OPS_LOG = [
    "2020-07-21 21:11:54,386 - INFO - Stopping categories::  [TEST].     Message supplied with operation::       "
    "[No message provided.]",
    "2020-07-21 21:13:48,565 - INFO - Starting profiles::    [all].      Message supplied with operation::       "
    "[No message provided.]",
    "2020-07-21 21:13:35,827 - INFO - Starting profiles::    [ASRL_02].      Message supplied with operation::       "]


class ProfileManagerMonitorUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.profile = Mock(NAME="TEST_00", pid="1234")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.profilemanager_monitor.logging.Formatter.__init__', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager_monitor.logging.handlers')
    def test_init_logger__returns_logger_instance(self, *_):
        logger = profilemanager_monitor.init_logger()
        self.assertEqual("enmutils_int.lib.services.profilemanager_monitor", logger.name)

    @patch('enmutils_int.lib.services.profilemanager_monitor.logging.Formatter.__init__',
           side_effect=Exception("Error"))
    def test_init_logger__raises_runtime_error(self, _):
        self.assertRaises(RuntimeError, profilemanager_monitor.init_logger)

    @patch('enmutils_int.lib.services.profilemanager_monitor.process.get_profile_daemon_pid', return_value=["1234"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_profile_process__process_found(self, mock_debug, _):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.get_profile_process(TEST_PROFILE)
        self.assertEqual(2, mock_debug.call_count)
        self.assertEqual(0, len(profilemanager_monitor.DEAD_PROFILES))

    @patch('enmutils_int.lib.services.profilemanager_monitor.process.get_profile_daemon_pid', return_value=[])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_profile_process__adds_dead_process(self, mock_debug, _):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.get_profile_process(TEST_PROFILE)
        self.assertEqual(2, mock_debug.call_count)
        self.assertEqual(1, len(profilemanager_monitor.DEAD_PROFILES))

    @patch('enmutils_int.lib.services.profilemanager_monitor.timestamp.convert_str_to_datetime_object',
           return_value=datetime.now())
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries',
           return_value=["2020-01-01 00:01:12,634 DEBUG"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_no_longer_logging_profile__still_active(self, mock_debug, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.get_no_longer_logging_profile(TEST_PROFILE)
        mock_debug.assert_any_call("Checking log entry: [2020-01-01 00:01:12] if datetime object.")
        self.assertEqual(0, len(profilemanager_monitor.DEAD_PROFILES))

    @patch('enmutils_int.lib.services.profilemanager_monitor.timestamp.convert_str_to_datetime_object',
           return_value=datetime.strptime("2020-01-01 00:01:12", "%Y-%m-%d %H:%M:%S"))
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries',
           return_value=["2020-01-01 00:01:12,634 DEBUG", "<html>"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_no_longer_logging_profile__dead_profile(self, mock_debug, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.get_no_longer_logging_profile(TEST_PROFILE)
        mock_debug.assert_any_call("Checking log entry: [2020-01-01 00:01:12] if datetime object.")
        self.assertEqual(1, len(profilemanager_monitor.DEAD_PROFILES))

    @patch('enmutils_int.lib.services.profilemanager_monitor.timestamp.convert_str_to_datetime_object',
           return_value="string")
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries',
           return_value=["2020-01-01 00:01:12,634 DEBUG"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_no_longer_logging_profile__fails_to_convert(self, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.get_no_longer_logging_profile(TEST_PROFILE)
        self.assertEqual(0, len(profilemanager_monitor.DEAD_PROFILES))

    @patch('enmutils_int.lib.services.profilemanager_monitor.commands.getstatusoutput', return_value=(0, "Line\nLine1"))
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_collect_log_entries__success(self, mock_debug, _):
        self.assertEqual(2, len(profilemanager_monitor.collect_log_entries(TEST_PROFILE, "cmd", "file")))
        mock_debug.assert_called_with("Completed querying file for any entries containing profile: {0}.".format(
            TEST_PROFILE))

    @patch('enmutils_int.lib.services.profilemanager_monitor.commands.getstatusoutput', return_value=(256, ""))
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_collect_log_entries__command_fails(self, mock_debug, _):
        self.assertEqual(0, len(profilemanager_monitor.collect_log_entries(TEST_PROFILE, "cmd", "file")))
        mock_debug.assert_any_call("Unable to retrieve file entries for profile: [{0}], rc: [256], output: [].".format(
            TEST_PROFILE))

    @patch('enmutils_int.lib.services.profilemanager_monitor.persistence.get', return_value="Error")
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries', return_value=["Line"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_log_log_entries__adds_log_entries_and_persisted_errors(self, mock_debug, *_):
        profilemanager_monitor.log_log_entries(TEST_PROFILE)
        self.assertEqual(11, mock_debug.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries', return_value=["Line"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_log_log_entries__no_persisted_errors(self, mock_debug, *_):
        profilemanager_monitor.log_log_entries(TEST_PROFILE)
        self.assertEqual(10, mock_debug.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.get_profile_process')
    @patch('enmutils_int.lib.services.profilemanager_monitor.get_no_longer_logging_profile',
           side_effect=lambda _: setattr(profilemanager_monitor, 'DEAD_PROFILES', [TEST_PROFILE]))
    def test_update_list_of_no_longer_active_profiles__inactive_profile(self, mock_no_longer_logging,
                                                                        mock_get_process):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.update_list_of_no_longer_active_profiles(TEST_PROFILE, self.profile)
        self.assertEqual(1, mock_no_longer_logging.call_count)
        self.assertEqual(1, mock_get_process.call_count)
        self.assertEqual(1, len(profilemanager_monitor.DEAD_PROFILES))

    @patch('enmutils_int.lib.services.profilemanager_monitor.get_profile_process')
    @patch('enmutils_int.lib.services.profilemanager_monitor.get_no_longer_logging_profile')
    def test_update_list_of_no_longer_active_profiles__skips_additional_checks_if_profile_dead(
            self, mock_no_longer_logging, mock_get_process):
        profilemanager_monitor.DEAD_PROFILES = [TEST_PROFILE]
        profilemanager_monitor.update_list_of_no_longer_active_profiles(TEST_PROFILE, self.profile)
        self.assertEqual(0, mock_no_longer_logging.call_count)
        self.assertEqual(0, mock_get_process.call_count)

    def test_determine_last_related_log_entry__selects_latest_operation(self):
        result = profilemanager_monitor.determine_last_related_log_entry(WORKLOAD_OPS_LOG)
        self.assertEqual(result, WORKLOAD_OPS_LOG[1])

    def test_determine_last_related_log_entry__success(self):
        result = profilemanager_monitor.determine_last_related_log_entry(WORKLOAD_OPS_LOG[0:1])
        self.assertEqual(result, WORKLOAD_OPS_LOG[0])

    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries', return_value=[])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_expected_state_of_profile__no_recent_log_operations(self, mock_debug, mock_collect):
        self.assertEqual("restart", profilemanager_monitor.get_expected_state_of_profile(TEST_PROFILE))
        mock_debug.assert_called_with("Completed check of {0} for recent workload operations related to profile: [{1}]"
                                      "".format(profilemanager_monitor.WORKLOAD_OPS_LOG, TEST_PROFILE))
        self.assertEqual(3, mock_collect.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.determine_last_related_log_entry',
           return_value=WORKLOAD_OPS_LOG[0])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries', return_value=["line"])
    def test_get_expected_state_of_profile__recent_log_operations_stop(self, mock_collect, *_):
        self.assertEqual("stop", profilemanager_monitor.get_expected_state_of_profile(TEST_PROFILE))
        self.assertEqual(3, mock_collect.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.determine_last_related_log_entry',
           return_value=WORKLOAD_OPS_LOG[1])
    @patch('enmutils_int.lib.services.profilemanager_monitor.collect_log_entries', return_value=["line"])
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_get_expected_state_of_profile__recent_log_operations_restart(self, *_):
        self.assertEqual("restart", profilemanager_monitor.get_expected_state_of_profile(TEST_PROFILE))

    @patch('enmutils_int.lib.services.profilemanager_monitor.process.kill_spawned_process')
    def test_profile_clean_up__success(self, mock_kill):
        profilemanager_monitor.profile_clean_up(self.profile)
        mock_kill.assert_called_with(self.profile.NAME, self.profile.pid)

    @patch('enmutils_int.lib.services.profilemanager_monitor.process.kill_spawned_process',
           side_effect=Exception("Error"))
    def test_profile_clean_up__teardown_called_on_failure(self, mock_kill):
        profilemanager_monitor.profile_clean_up(self.profile)
        mock_kill.assert_called_with(self.profile.NAME, self.profile.pid)
        self.assertEqual(1, self.profile.teardown.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.commands.getstatusoutput', return_value=(0, "unsupported"))
    @patch('enmutils_int.lib.services.profilemanager_monitor.profile_clean_up')
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_trigger_profile_operation__restarts_profile_successfully(self, mock_debug, *_):
        profilemanager_monitor.trigger_profile_operation(TEST_PROFILE, self.profile, "restart")
        mock_debug.assert_any_call("Completed workload restart profile: [{0}]".format(TEST_PROFILE))

    @patch('enmutils_int.lib.services.profilemanager_monitor.commands.getstatusoutput', return_value=(256, ""))
    @patch('enmutils_int.lib.services.profilemanager_monitor.profile_clean_up')
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_trigger_profile_operation__restarts_profile_failure(self, mock_debug, *_):
        profilemanager_monitor.trigger_profile_operation(TEST_PROFILE, self.profile, "start")
        mock_debug.assert_any_call("Unable to restart profile, rc: [256], output: [].")

    @patch('enmutils_int.lib.services.profilemanager_monitor.commands.getstatusoutput')
    @patch('enmutils_int.lib.services.profilemanager_monitor.profile_clean_up')
    def test_trigger_profile_operation__stop_profile(self, mock_clean_up, mock_get_status):
        profilemanager_monitor.trigger_profile_operation(TEST_PROFILE, self.profile, "stop")
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(0, mock_get_status.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.profile_clean_up')
    def test_confirm_profile_state__correct_state(self, mock_clean_up, mock_trigger):
        self.profile.state = "STOPPING"
        self.profile.status = "ERROR"
        profilemanager_monitor.confirm_profile_state(TEST_PROFILE, self.profile, "stop")
        self.assertEqual(0, mock_clean_up.call_count)
        self.assertEqual(0, mock_trigger.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.profile_clean_up')
    def test_confirm_profile_state__stop_invalid_state(self, mock_clean_up, mock_trigger):
        self.profile.state = "STARTING"
        self.profile.status = "OK"
        profilemanager_monitor.confirm_profile_state(TEST_PROFILE, self.profile, "stop")
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(0, mock_trigger.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.profile_clean_up')
    def test_confirm_profile_state__restart_invalid_state(self, mock_clean_up, mock_trigger):
        self.profile.state = "STOPPING"
        self.profile.status = "DEAD"
        profilemanager_monitor.confirm_profile_state(TEST_PROFILE, self.profile, "restart")
        self.assertEqual(0, mock_clean_up.call_count)
        self.assertEqual(1, mock_trigger.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    def test_verify_profile_state__no_inactive_profiles(self, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.logger.handlers = [Mock()]
        self.profile.status = "WARNING"
        self.assertEqual([], profilemanager_monitor.verify_profile_state([self.profile]))

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    def test_verify_profile_state__skips_completed(self, mock_update, mock_check_if_profile_has_completed, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.logger.handlers = [Mock()]
        self.profile.status = "WARNING"
        self.profile.state = "COMPLETED"
        self.assertEqual([], profilemanager_monitor.verify_profile_state([self.profile]))
        self.assertEqual(0, mock_update.call_count)
        self.assertEqual(0, mock_check_if_profile_has_completed.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_monitor.log_log_entries')
    @patch('enmutils_int.lib.services.profilemanager_monitor.get_expected_state_of_profile')
    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.confirm_profile_state')
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    def test_verify_profile_state__triggers_restart(self, mock_update, mock_confirm, mock_trigger, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.logger.handlers = [Mock()]
        self.profile.status = "WARNING"
        self.profile.state = "STARTING"
        mock_update.side_effect = lambda x, y: setattr(profilemanager_monitor, 'DEAD_PROFILES', [TEST_PROFILE])
        self.assertEqual([TEST_PROFILE], profilemanager_monitor.verify_profile_state([self.profile]))
        self.assertEqual(1, mock_confirm.call_count)
        self.assertEqual(1, mock_trigger.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_monitor.log_log_entries')
    @patch('enmutils_int.lib.services.profilemanager_monitor.get_expected_state_of_profile')
    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.confirm_profile_state')
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    def test_verify_profile_state__does_not_trigger_restart_if_excluded(
            self, mock_update, mock_confirm, mock_trigger, *_):
        original_excluded = profilemanager_monitor.EXCLUDED_PROFILES
        profilemanager_monitor.EXCLUDED_PROFILES = [self.profile.NAME]
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.logger.handlers = [Mock()]
        self.profile.status = "WARNING"
        self.profile.state = "STARTING"
        mock_update.side_effect = lambda x, y: setattr(profilemanager_monitor, 'DEAD_PROFILES', [TEST_PROFILE])
        self.assertEqual([], profilemanager_monitor.verify_profile_state([self.profile]))
        self.assertEqual(0, mock_confirm.call_count)
        self.assertEqual(0, mock_trigger.call_count)
        profilemanager_monitor.EXCLUDED_PROFILES = original_excluded

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    @patch('enmutils_int.lib.services.profilemanager_monitor.init_logger')
    def test_verify_profile_state__calls_init_log_if_no_handlers(self, mock_init, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.logger.handlers = []
        self.profile.status = "WARNING"
        profilemanager_monitor.verify_profile_state([self.profile])
        self.assertEqual(1, mock_init.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed', return_value=False)
    @patch('enmutils_int.lib.services.profilemanager_monitor.init_logger')
    @patch('enmutils_int.lib.services.profilemanager_monitor.log_log_entries')
    @patch('enmutils_int.lib.services.profilemanager_monitor.get_expected_state_of_profile')
    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.confirm_profile_state')
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    def test_verify_profile_state__mock_update_not_called_if_listed_as_dead(self, mock_update, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.logger.handlers = [Mock()]
        self.profile.status = "DEAD"
        profilemanager_monitor.verify_profile_state([self.profile])
        self.assertEqual(0, mock_update.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.services.profilemanager_monitor.check_if_profile_has_completed',
           side_effect=[False, True])
    @patch('enmutils_int.lib.services.profilemanager_monitor.init_logger')
    @patch('enmutils_int.lib.services.profilemanager_monitor.log_log_entries')
    @patch('enmutils_int.lib.services.profilemanager_monitor.get_expected_state_of_profile')
    @patch('enmutils_int.lib.services.profilemanager_monitor.trigger_profile_operation')
    @patch('enmutils_int.lib.services.profilemanager_monitor.confirm_profile_state')
    @patch('enmutils_int.lib.services.profilemanager_monitor.update_list_of_no_longer_active_profiles')
    def test_verify_profile_state__excludes_profile_if_initially_running_but_is_completed_later(self, mock_update, *_):
        profilemanager_monitor.DEAD_PROFILES = []
        profilemanager_monitor.EXCLUDED_PROFILES = []
        profilemanager_monitor.logger.handlers = [Mock()]
        profile1 = Mock(status="RUNNING", NAME="profile1")
        profile2 = Mock(status="RUNNING", NAME="profile2")
        profilemanager_monitor.verify_profile_state([profile1, profile2])
        self.assertEqual(1, mock_update.call_count)

    @patch('enmutils_int.lib.services.profilemanager_monitor.persistence.get')
    def test_check_if_profile_has_completed__returns_true_if_profile_completed(self, mock_get):
        mock_get.return_value = Mock(state="COMPLETED", status="OK")
        self.assertTrue(profilemanager_monitor.check_if_profile_has_completed("some_profile"))

    @patch('enmutils_int.lib.services.profilemanager_monitor.persistence.get')
    def test_check_if_profile_has_completed__returns_false_if_profile_still_running(self, mock_get):
        mock_get.return_value = Mock(state="RUNNING", status="OK")
        self.assertFalse(profilemanager_monitor.check_if_profile_has_completed("some_profile"))

    @patch('enmutils_int.lib.services.profilemanager_monitor.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.profilemanager_monitor.logger.debug')
    def test_check_if_profile_has_completed__returns_false_if_profile_no_longer_running(self, mock_debug, *_):
        self.assertTrue(profilemanager_monitor.check_if_profile_has_completed("some_profile"))
        mock_debug.assert_any_call("Profile key not found in persistence - profile no longer running")


if __name__ == '__main__':
    unittest2.main(verbosity=2)
