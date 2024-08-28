#!/usr/bin/env python
import time
from datetime import datetime, timedelta

import unittest2
from mock import patch, Mock, call, MagicMock
from pytz import timezone, utc

from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from paramiko import SSHException
from enmutils_int.lib.pm_nbi import Fls
from enmutils_int.lib.profile_flows.pm_flows import pm_fls_nbi_profile
from enmutils_int.lib.workload.pm_26 import PM_26
from enmutils_int.lib.workload.pm_28 import PM_28
from enmutils_int.lib.workload.pm_45 import PM_45
from testslib import unit_test_utils


class PmFlsNbiProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(username="TestUser")
        self.fls = Fls(user=self.user)
        self.profile = pm_fls_nbi_profile.PmFlsNbiProfile()
        self.profile.NAME = "TEST"
        self.profile.USER_ROLES = ["PM_NBI_Operator"]
        self.profile.SCHEDULED_TIMES_STRINGS = ["{0}:{1}:00".format(hour, minute) for hour in range(00, 24)
                                                for minute in range(5, 60, 15)]
        self.profile.KEYPAIR_FILE = "keypair"
        self.profile.DATA_TYPES = ["PM_STATISTICAL", "PM_CELLTRACE", "PM_CTUM"]
        self.profile.N_SFTP_THREADS = 10
        self.profile.JOIN_QUEUE_TIMEOUT = 1
        self.profile.SFTP_FETCH_TIME_IN_MINS = 15
        self.profile.ROP_INTERVAL = 15
        self.profile.OFFSET = 1
        self.time_remaining_for_sftp = 60
        self.profile.active_scripting_service_ip_list = ["ip_a", "ip_b"]

        self.profile.nbi_transfer_stats[self.user.username] = {"nbi_transfer_size": 0,
                                                               "nbi_transfer_file_count": 0,
                                                               "nbi_transfer_time": 0,
                                                               "nbi_fls_file_count": 0}
        self.profile.users = [self.user]
        self.profile.DATA_TYPES_UPDATE_TIME = "00:00"

        start_time = "2018-02-22T18:30:00"
        end_time = "2018-02-22T18:45:00"
        self.time_now = 1519327842.323188
        self.tz = timezone("Europe/Dublin")
        self.collection_times = {"start_time_of_iteration": self.time_now - 10,
                                 "start": start_time,
                                 "end": end_time,
                                 "time_range": (start_time, end_time),
                                 "rop_interval": self.profile.ROP_INTERVAL}

    @staticmethod
    def get_seconds_since_epoch(datetime_value):
        return (datetime_value - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()

    def tearDown(self):
        unit_test_utils.tear_down()

    # safe_teardown test

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_safe_teardown__on_physical(self, mock_run_local_cmd, mock_run_cmd_on_ms, *_):
        pm_fls_nbi_profile.safe_teardown(self.profile,
                                         self.profile.KILL_RUNNING_SFTP_PROCESSES,
                                         self.profile.SFTP_PIDS_FILE,
                                         self.profile.REMOVE_NBI_USER_DIR)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(4, mock_run_cmd_on_ms.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_safe_teardown__on_cenm_cloud(self, mock_run_local_cmd, mock_run_cmd_on_ms, *_):
        pm_fls_nbi_profile.safe_teardown(self.profile,
                                         self.profile.KILL_RUNNING_SFTP_PROCESSES,
                                         self.profile.SFTP_PIDS_FILE,
                                         self.profile.REMOVE_NBI_USER_DIR)
        self.assertEqual(4, mock_run_local_cmd.call_count)
        self.assertEqual(0, mock_run_cmd_on_ms.call_count)

    # tq_task_executor tests

    def test_tq_task_executor_call_sftp_task(self):
        sftp_task = Mock()
        sftp_task.__name__ = "sftp_nbi_files"
        task_set = (sftp_task, "some_batch_file_name", "svc-2-scripting_ip", self.user.username)
        pm_fls_nbi_profile.tq_task_executor(task_set, self.profile)
        sftp_task.assert_has_calls([call("some_batch_file_name", "svc-2-scripting_ip", self.user.username,
                                         self.profile)])

    def test_tq_task_executor_call_monitor(self):
        monitor_task = Mock()
        monitor_task.__name__ = "monitor_sftp_file_transfer"
        task_set = (monitor_task, {"blah1": "blah2"}, self.user.username, "")
        pm_fls_nbi_profile.tq_task_executor(task_set, self.profile)
        monitor_task.assert_has_calls([call({"blah1": "blah2"}, self.user.username, "", self.profile)])

    # sftp_nbi_files tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_sftp_nbi_files__is_successful(self, mock_run_cmd_on_ms, mock_read_lines_from_file, mock_debug_log,
                                           mock_add_error, *_):
        mock_run_cmd_on_ms.return_value = Mock(rc=0, stdout="Success")
        mock_read_lines_from_file.return_value = [Mock(), Mock()]
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {}
        pm_fls_nbi_profile.sftp_nbi_files("batch_file_01", "ip_address", self.user.username, self.profile)
        self.assertTrue(mock_run_cmd_on_ms.called)
        self.assertEqual(mock_read_lines_from_file.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_sftp_nbi_files__is_successful_on_non_physical_deployments(self, mock_run_local_cmd,
                                                                       mock_read_lines_from_file, mock_debug_log,
                                                                       mock_add_error, *_):
        mock_run_local_cmd.return_value = Mock(rc=0, stdout="Success")
        mock_read_lines_from_file.return_value = [Mock(), Mock()]
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {}
        pm_fls_nbi_profile.sftp_nbi_files("batch_file_01", "ip_address", self.user.username, self.profile)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertEqual(mock_read_lines_from_file.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_sftp_nbi_files__is_raises_environerror_if_sftp_attempt_results_in_permission_denied(
            self, mock_run_cmd_on_ms, mock_read_lines_from_file, mock_debug_log, mock_add_error, *_):
        mock_run_cmd_on_ms.return_value = Mock(rc=1, stdout="Permission denied")
        mock_read_lines_from_file.return_value = [Mock(), Mock()]
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch0": 2}
        with self.assertRaises(EnvironError) as environ_error:
            pm_fls_nbi_profile.sftp_nbi_files("batch_file", "ip_address", self.user.username, self.profile)
        message = ("'Permission denied' encountered while sftp'ing files from ip_address which could mean "
                   "profile user is not authorized to 1) access scripting VM, or "
                   "2) access files on the PMIC mountpoints on the NAS.")
        self.assertEqual(message, environ_error.exception.message)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)
        self.assertEqual(mock_read_lines_from_file.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_sftp_nbi_files__is_raises_environerror_if_sftp_attempt_results_in_connection_reset(
            self, mock_run_cmd_on_ms, mock_read_lines_from_file, mock_debug_log, mock_add_error, *_):
        mock_run_cmd_on_ms.return_value = Mock(rc=1, stdout="Connection reset by peer")
        mock_read_lines_from_file.return_value = [Mock(), Mock()]
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch0": 2}
        with self.assertRaises(EnmApplicationError) as enmapplication_error:
            pm_fls_nbi_profile.sftp_nbi_files("batch_file", "ip_address", self.user.username, self.profile)
        self.assertEqual("Connection reset by peer (ip_address)", enmapplication_error.exception.message)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 2)
        self.assertEqual(mock_read_lines_from_file.call_count, 2)
        self.assertEqual(mock_debug_log.call_count, 10)
        self.assertEqual(mock_add_error.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_sftp_nbi_files__is_raises_enmapplication_error_if_batch_file_is_not_exist(
            self, mock_run_cmd_on_ms, mock_read_lines_from_file, mock_debug_log, mock_add_error, *_):
        mock_run_cmd_on_ms.return_value = Mock(rc=1, stdout="Couldn't stat remote file: No such file or directory")
        mock_read_lines_from_file.return_value = [Mock(), Mock()]
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch0": 2}
        with self.assertRaises(EnvironError) as environ_error:
            pm_fls_nbi_profile.sftp_nbi_files("batch_file", "ip_address", self.user.username, self.profile)
        self.assertEqual("Unable to find files via scripting VM (ip_address)", environ_error.exception.message)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)
        self.assertEqual(mock_read_lines_from_file.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.read_lines_from_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_sftp_nbi_files__is_raises_environerror_if_sftp_attempt_results_in_other_error(
            self, mock_run_cmd_on_ms, mock_read_lines_from_file, mock_debug_log, mock_add_error, *_):
        mock_run_cmd_on_ms.return_value = Mock(rc=1, stdout="Other problem")
        mock_read_lines_from_file.return_value = [Mock(), Mock()]
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch0": 2}
        with self.assertRaises(EnvironError) as environ_error:
            pm_fls_nbi_profile.sftp_nbi_files("batch_file", "ip_address", self.user.username, self.profile)
        self.assertEqual("Error occurred during sftp of files from ip_address - see log for details",
                         environ_error.exception.message)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)
        self.assertEqual(mock_read_lines_from_file.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)

    # monitor_sftp_file_transfer tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.any_sftp_processes_still_running", return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.safe_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.check_that_sftp_processes_are_complete", return_value=True)
    def test_monitor_sftp_file_transfer__all_processes_gone_after_iteration_ends(self, *_):
        self.assertTrue(pm_fls_nbi_profile.monitor_sftp_file_transfer(self.collection_times, self.user.username, "",
                                                                      self.profile))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.any_sftp_processes_still_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.safe_teardown")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.check_that_sftp_processes_are_complete",
           return_value=False)
    def test_monitor_sftp_file_transfer__raises_environerror_when_all_processes_not_gone_after_loop_ends(
            self, mock_check_that_sftp_processes_are_complete, mock_time, *_):
        mock_time.return_value = self.time_now
        self.assertRaises(EnvironError, pm_fls_nbi_profile.monitor_sftp_file_transfer, self.collection_times,
                          self.user.username, "blah", self.profile)

        time_elapsed_since_start_of_iteration = int(datetime.now().time().strftime('%s')) - int(datetime.strptime(self.collection_times['end'],
                                                                                                                  '%Y-%m-%dT%H:%M:%S').time().strftime('%s'))
        total_time_of_iteration_in_secs = 900
        grace_time_at_end_of_iteration = 60
        checking_interval = 10
        time_remaining_for_sftp_transfer = (total_time_of_iteration_in_secs -
                                            time_elapsed_since_start_of_iteration -
                                            grace_time_at_end_of_iteration)

        possible_number_of_checks = (total_time_of_iteration_in_secs -
                                     time_elapsed_since_start_of_iteration -
                                     grace_time_at_end_of_iteration) / checking_interval

        mock_check_that_sftp_processes_are_complete.assert_called_with(self.profile, self.user.username, self.time_now,
                                                                       checking_interval, possible_number_of_checks,
                                                                       time_remaining_for_sftp_transfer)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.any_sftp_processes_still_running")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    def test_check_that_sftp_processes_are_complete__is_successful(
            self, mock_time, mock_any_sftp_processes_still_running, _):
        mock_any_sftp_processes_still_running.side_effect = [False, False, False, False, False]
        mock_time.side_effect = [1001, 1011, 1021, 1031, 1041]
        pm_fls_nbi_profile.check_that_sftp_processes_are_complete(self.profile, self.user.username, 1000, 10, 5, 80)
        self.assertEqual(mock_time.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.any_sftp_processes_still_running")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    def test_check_that_sftp_processes_are_complete__can_cope_with_sleeps_greater_than_10s(
            self, mock_time, mock_sleep, *_):
        mock_time.side_effect = [1005, 1025, 1025, 1045, 1065, 1085]
        pm_fls_nbi_profile.check_that_sftp_processes_are_complete(self.profile, self.user.username, 1000, 10, 4, 120)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.any_sftp_processes_still_running")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    def test_check_that_sftp_processes_are_complete__cannot_cope_with_sleeps_greater_than_10s(
            self, mock_time, mock_sleep, *_):
        mock_time.side_effect = [1005, 1025, 1025, 1045, 1065, 1085]
        pm_fls_nbi_profile.check_that_sftp_processes_are_complete(self.profile, self.user.username, 1000, 10, 4, 200)
        self.assertEqual(mock_sleep.call_count, 1)

    # initiate_profile_and_environment tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.partial")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.set_environment_type_attributes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.Fls")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.clear_sftp_pid_file")
    def test_initiate_profile_and_environment__is_successful(
            self, mock_clear_sftp_pid_file, mock_create_users, mock_fls, mock_run_local_cmd, mock_command, *_):
        some_mock = Mock()
        mock_fls.return_value = some_mock
        mock_create_users.return_value = [Mock(username=1), Mock(username=2)]
        self.assertEqual([(some_mock, 0), (some_mock, 20)], self.profile.initiate_profile_and_environment())

        self.assertEqual(mock_clear_sftp_pid_file.call_count, 2)
        mock_run_local_cmd.assert_called_with(mock_command.return_value)
        mock_command.assert_called_with("rm -rf /dev/shm/pm_nbi/TEST*")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.set_environment_type_attributes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.create_users",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    def test_initiate_profile_and_environment__raises_enmapplicationerror_if_create_users_throws_exception(
            self, mock_command, *_):
        self.assertRaises(EnmApplicationError, self.profile.initiate_profile_and_environment)
        mock_command.assert_called_with("rm -rf /dev/shm/pm_nbi/TEST*")

    # set_environment_type_attributes tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.get_list_of_scripting_service_ips")
    def test_set_environment_type_attributes__is_successful(self, mock_get_list_of_scripting_service_ips):
        self.profile.set_environment_type_attributes()
        self.assertTrue(mock_get_list_of_scripting_service_ips.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.get_list_of_scripting_service_ips")
    def test_set_environment_type_attributes__raises_environerror_if_scripting_ips_not_existed(
            self, mock_get_list_of_scripting_service_ips):
        mock_get_list_of_scripting_service_ips.return_value = []
        self.assertRaises(EnvironError, self.profile.set_environment_type_attributes)
        self.assertTrue(mock_get_list_of_scripting_service_ips)

    # check_pm_nbi_directory tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.filesystem.does_dir_exist")
    def test_check_pm_nbi_directory__doesnt_exist(self, mock_does_dir_exist, mock_run_local_cmd, *_):
        mock_does_dir_exist.side_effect = [True, False]
        self.profile.check_pm_nbi_directory(self.user.username)
        self.assertFalse(mock_run_local_cmd.called)

        self.profile.check_pm_nbi_directory(self.user.username)
        self.assertEqual(1, mock_run_local_cmd.call_count)

    # clear_pm_nbi_directory tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms", return_value=Mock(ok=1))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd", return_value=Mock(ok=1))
    def test_clear_pm_nbi_directory__is_successful_on_physical(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                               mock_command, _):
        self.profile.clear_pm_nbi_directory(self.user.username)
        mock_run_local_cmd.assert_called_with(mock_command.return_value)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)
        mock_command.assert_called_with("find /dev/shm/pm_nbi/TestUser/batch_files -type f -print0 | "
                                        "xargs -0 -P 0 rm -f")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms", return_value=Mock(ok=0))
    def test_clear_pm_nbi_directory__environ_error_on_physical(self, mock_run_cmd_on_ms, mock_command, *_):
        self.assertRaises(EnvironError, self.profile.clear_pm_nbi_directory, self.user.username)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)
        mock_command.assert_called_with("find /dev/shm/pm_nbi/TestUser/batch_files -type f -print0 | "
                                        "xargs -0 -P 0 rm -f")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd", return_value=Mock(ok=0))
    def test_clear_pm_nbi_directory__is_unsuccessful(self, mock_run_local_cmd, mock_command, *_):
        self.assertRaises(EnvironError, self.profile.clear_pm_nbi_directory, self.user.username)
        mock_run_local_cmd.assert_called_with(mock_command.return_value)
        mock_command.assert_called_with("find /dev/shm/pm_nbi/TestUser/batch_files -type f -print0 | "
                                        "xargs -0 -P 0 rm -f")

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms", return_value=Mock(ok=1))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd", return_value=Mock(ok=1))
    def test_clear_pm_nbi_directory__is_successful_on_cenm_cloud(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                                 mock_command, _):
        self.profile.clear_pm_nbi_directory(self.user.username)
        mock_run_local_cmd.assert_called_with(mock_command.return_value)
        self.assertFalse(mock_run_cmd_on_ms.called)
        mock_command.assert_called_with("find /dev/shm/pm_nbi/TestUser/batch_files -type f -print0 | "
                                        "xargs -0 -P 0 rm -f")

    # clear_sftp_pid_file tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_clear_sftp_pid_file__success_on_physical(self, mock_run_cmd_on_ms, mock_run_local_cmd, mock_command, *_):
        self.profile.clear_sftp_pid_file(self.user.username)
        mock_run_local_cmd.assert_called_with(mock_command.return_value)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_clear_sftp_pid_file__success_on_cenm_cloud(self, mock_run_cmd_on_ms, mock_run_local_cmd, mock_command, *_):
        self.profile.clear_sftp_pid_file(self.user.username)
        mock_run_local_cmd.assert_called_with(mock_command.return_value)
        self.assertFalse(mock_run_cmd_on_ms.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_clear_sftp_pid_file__does_not_run_command(self, mock_run_local_cmd, *_):
        self.profile.clear_sftp_pid_file(self.user.username)
        self.assertFalse(mock_run_local_cmd.called)

    # get_files_to_collect tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    def test_get_files_to_collect__is_successful(self, mock_debug_log):
        fls = MagicMock()
        self.profile.data_type_file_id_dict = {'PM_CELLTRACE': [0, None], 'PM_STATISTICAL': [2, None], 'PM_CTUM': [0, None]}
        files_collected = ["PM_Stats_path_1", "PM_Stats_path_2", "PM_Ctum_file"]
        fls.get_pmic_rop_files_location.side_effect = [([], 0, None), (["PM_Stats_path_1", "PM_Stats_path_2"], 1234, "time_1"), (["PM_Ctum_file"], 2345, "time_2")]
        files, _ = pm_fls_nbi_profile.get_files_to_collect(self.profile, fls)
        self.assertEqual(fls.get_pmic_rop_files_location.call_count, 3)
        self.assertEqual(files, files_collected)
        self.assertEqual(mock_debug_log.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    def test_get_files_to_collect__is_unsuccessful(self, mock_time, mock_debug_log, mock_add_error_as_exception):
        fls = MagicMock()
        mock_time.side_effect = 0, 400
        self.profile.data_type_file_id_dict = {'PM_CELLTRACE': [0, None], 'PM_STATISTICAL': [2, None],
                                               'PM_CTUM': [0, None]}
        files_collected = []
        fls.get_pmic_rop_files_location.side_effect = [([], 0, None),
                                                       (["PM_Stats_path_1", "PM_Stats_path_2"], 1234, "time_1"),
                                                       (["PM_Ctum_file"], 2345, "time_2")]
        files, _ = pm_fls_nbi_profile.get_files_to_collect(self.profile, fls)

        self.assertEqual(fls.get_pmic_rop_files_location.call_count, 1)
        self.assertEqual(files, files_collected)
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_time.call_count, 2)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_get_files_to_collect__logs_exception_and_continues(self, mock_add_error_as_exception, mock_debug_log):
        fls = MagicMock()
        self.profile.data_type_file_id_dict = {'PM_CELLTRACE': [0, None], 'PM_STATISTICAL': [0, None], 'PM_CTUM': [0, None]}
        files_collected = ["PM_Stats_path_1", "PM_Stats_path_2", "PM_Ctum_file"]
        fls.get_pmic_rop_files_location.side_effect = [Exception, (["PM_Stats_path_1", "PM_Stats_path_2"], 1234, "time_1"), (["PM_Ctum_file"], 2345, "time_2")]
        files, _ = pm_fls_nbi_profile.get_files_to_collect(self.profile, fls)
        self.assertEqual(fls.get_pmic_rop_files_location.call_count, 3)
        self.assertEqual(files, files_collected)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 5)

    # create_and_execute_sftp_threads tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.collect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.log_results_of_nbi_transfer")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.ThreadQueue")
    def test_create_and_execute_sftp_threads__returns_false_if_thread_exceptions_occur(
            self, mock_thread_queue, mock_log_results, *_):
        mock_thread_queue.return_value = Mock()
        mock_thread_queue.return_value.exceptions = [Exception]
        result = pm_fls_nbi_profile.create_and_execute_sftp_threads(self.profile, self.fls, self.collection_times)
        self.assertFalse(result)
        self.assertEqual(mock_log_results.call_count, 1)
        self.assertTrue(mock_thread_queue.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.collect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.log_results_of_nbi_transfer")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.ThreadQueue")
    def test_create_and_execute_sftp_threads__returns_true_if_no_thread_exceptions_occur(
            self, mock_thread_queue, mock_log_results, *_):
        mock_thread_queue.return_value = Mock()
        mock_thread_queue.return_value.exceptions = []
        result = pm_fls_nbi_profile.create_and_execute_sftp_threads(self.profile, self.fls, self.collection_times)
        self.assertTrue(result)
        self.assertEqual(mock_log_results.call_count, 1)
        self.assertTrue(mock_thread_queue.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.log_results_of_nbi_transfer")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.collect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.ThreadQueue")
    def test_create_and_execute_sftp_threads__returns_false_if_there_are_no_active_scripting_vms(
            self, mock_thread_queue, *_):
        self.profile.active_scripting_service_ip_list = []
        self.assertFalse(pm_fls_nbi_profile.create_and_execute_sftp_threads(self.profile, self.fls, self.collection_times))
        self.assertFalse(mock_thread_queue.called)

    # get_active_scripting_service_ip_list tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.are_ssh_credentials_valid")
    def test_get_active_scripting_service_ip_list__returns_all_ips_if_all_scripting_vms_are_active(
            self, mock_are_ssh_credentials_valid, mock_debug_log, *_):
        self.profile.scp_scripting_service_ip_list = ["ip_1", "ip_2"]
        mock_are_ssh_credentials_valid.return_value = True
        self.assertEqual(self.profile.scp_scripting_service_ip_list,
                         self.profile.get_active_scripting_service_ip_list())
        self.assertEqual(mock_are_ssh_credentials_valid.call_count, 2)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.are_ssh_credentials_valid")
    def test_get_active_scripting_service_ip_list__returns_empty_if_all_scripting_vms_are_inactive(
            self, mock_are_ssh_credentials_valid, mock_debug_log, *_):
        self.profile.scp_scripting_service_ip_list = ["ip_1", "ip_2"]
        mock_are_ssh_credentials_valid.return_value = False
        self.assertRaises(EnvironError, self.profile.get_active_scripting_service_ip_list)
        self.assertEqual(mock_are_ssh_credentials_valid.call_count, 2)
        self.assertEqual(mock_debug_log.call_count, 3)

    # transfer_pmic_files_to_nbi tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.transfer_batch_files_to_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.perform_sftp_fetch",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "create_sftp_batch_files_on_server")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.get_list_of_files_from_fls")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "cleanup_pm_nbi_profile_artefacts")
    def test_transfer_pmic_files_to_nbi__is_successful_on_physical(
            self, mock_cleanup_pm_nbi_profile_artefacts, mock_get_list_of_files_from_fls,
            mock_create_sftp_batch_files_on_server, *_):
        fls = self.fls
        files = ["blah1", "blah2", "blah3", "blah4", "blah5", "blah6", "blah7", "blah8", "blah9", "blah10", "blah11", "blah12", "blah13", "blah14"]
        mock_get_list_of_files_from_fls.return_value = files
        self.assertTrue(self.profile.transfer_pmic_files_to_nbi(fls, self.collection_times))
        self.assertTrue(mock_cleanup_pm_nbi_profile_artefacts.called)
        self.assertTrue(mock_get_list_of_files_from_fls.called)
        mock_create_sftp_batch_files_on_server.assert_called_with(fls, files)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.transfer_batch_files_to_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.perform_sftp_fetch",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "create_sftp_batch_files_on_server")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.get_list_of_files_from_fls")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "cleanup_pm_nbi_profile_artefacts")
    def test_transfer_pmic_files_to_nbi__is_successful_on_cenm_cloud(
            self, mock_cleanup_pm_nbi_profile_artefacts, mock_get_list_of_files_from_fls,
            mock_create_sftp_batch_files_on_server, *_):
        fls = self.fls
        files = ["blah1", "blah2", "blah3", "blah4", "blah5", "blah6", "blah7", "blah8", "blah9", "blah10", "blah11",
                 "blah12", "blah13", "blah14"]
        mock_get_list_of_files_from_fls.return_value = files
        self.assertTrue(self.profile.transfer_pmic_files_to_nbi(fls, self.collection_times))
        self.assertTrue(mock_cleanup_pm_nbi_profile_artefacts.called)
        self.assertTrue(mock_get_list_of_files_from_fls.called)
        mock_create_sftp_batch_files_on_server.assert_called_with(fls, files)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.perform_sftp_fetch",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.transfer_batch_files_to_ms")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "create_sftp_batch_files_on_server")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.get_list_of_files_from_fls")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "cleanup_pm_nbi_profile_artefacts")
    def test_transfer_pmic_files_to_nbi__no_files_no_sftp_transfer(
            self, mock_cleanup_pm_nbi_profile_artefacts, mock_get_list_of_files_from_fls,
            mock_create_sftp_batch_files_on_server, *_):
        fls = self.fls
        files = []
        mock_get_list_of_files_from_fls.return_value = files
        self.profile.transfer_pmic_files_to_nbi(fls, self.collection_times)
        self.assertTrue(mock_cleanup_pm_nbi_profile_artefacts.called)
        self.assertTrue(mock_get_list_of_files_from_fls.called)
        self.assertFalse(mock_create_sftp_batch_files_on_server.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.create_and_execute_sftp_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.multitasking.create_single_process_and_execute_task")
    def test_transfer_pmic_files_to_nbi__raises_environerror_if_error_occurs_during_thread_creation(
            self, mock_create_single_process_and_execute_task, _):
        mock_create_single_process_and_execute_task.side_effect = Exception("Error")
        self.assertRaises(EnvironError, self.profile.perform_sftp_fetch, Mock(), self.collection_times)
        self.assertTrue(mock_create_single_process_and_execute_task.called)

    # transfer_batch_files_to_ms tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_transfer_batch_files_to_ms__is_host_physical_deployment(self, mock_run_local_cmd, mock_cache):
        mock_cache.get_ms_host.return_value = "ip"
        mock_cache.is_host_physical_deployment.return_value = True
        self.profile.transfer_batch_files_to_ms()
        mock_run_local_cmd.assert_called_with(
            "scp -r -o stricthostkeychecking=no /dev/shm/pm_nbi/ root@ip:/dev/shm/")
        self.assertTrue(mock_cache.get_ms_host.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_transfer_batch_files_to_ms__raises_environ_error(self, mock_run_local_cmd, mock_cache):
        mock_cache.get_ms_host.return_value = "ip"
        mock_run_local_cmd.side_effect = SSHException
        self.assertRaises(EnvironError, self.profile.transfer_batch_files_to_ms)
        mock_run_local_cmd.assert_called_with(
            "scp -r -o stricthostkeychecking=no /dev/shm/pm_nbi/ root@ip:/dev/shm/")
        self.assertTrue(mock_cache.get_ms_host.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    def test_transfer_batch_files_to_ms__raises_enm_application_error(self, mock_run_local_cmd, mock_cache):
        mock_cache.get_ms_host.return_value = "ip"
        mock_cache.is_host_physical_deployment.return_value = True
        mock_run_local_cmd.side_effect = Exception
        self.assertRaises(EnmApplicationError, self.profile.transfer_batch_files_to_ms)
        mock_run_local_cmd.assert_called_with(
            "scp -r -o stricthostkeychecking=no /dev/shm/pm_nbi/ root@ip:/dev/shm/")
        self.assertTrue(mock_cache.get_ms_host.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.clear_pm_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.clear_sftp_pid_file")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    def test_cleanup_pm_nbi_profile_artefacts__is_successful(self, mock_check_profile_memory_usage, *_):
        self.profile.cleanup_pm_nbi_profile_artefacts(self.fls)
        self.assertTrue(mock_check_profile_memory_usage.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.clear_pm_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.clear_sftp_pid_file")
    def test_cleanup_pm_nbi_profile_artefacts__raises_environerror_if_clear_pid_file_fails(
            self, mock_clear_sftp_pid_file, *_):
        mock_clear_sftp_pid_file.side_effect = Exception
        self.assertRaises(EnvironError,
                          self.profile.cleanup_pm_nbi_profile_artefacts, self.fls)
        self.assertTrue(mock_clear_sftp_pid_file.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.get_files_to_collect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.multitasking."
           "create_single_process_and_execute_task")
    def test_get_list_of_files_from_fls__raises_enmapplicationerror_if_exception_occurs_while_querying_fls(
            self, mock_create_single_process_and_execute_task, _):
        self.profile.data_type_file_id_dict = {data_type: 0 for data_type in self.profile.DATA_TYPES}
        mock_create_single_process_and_execute_task.side_effect = Exception("Error")
        self.assertRaises(EnmApplicationError, self.profile.get_list_of_files_from_fls, Mock(), self.collection_times)
        self.assertTrue(mock_create_single_process_and_execute_task.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.get_files_to_collect", return_value=[])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.multitasking."
           "create_single_process_and_execute_task")
    def test_get_list_of_files_from_fls__raises_environerror_if_no_files_reported_by_fls(
            self, mock_create_single_process_and_execute_task, _):
        self.profile.data_type_file_id_dict = {data_type: 0 for data_type in self.profile.DATA_TYPES}
        mock_create_single_process_and_execute_task.return_value = [], {}
        self.assertRaises(EnvironError, self.profile.get_list_of_files_from_fls, Mock(), self.collection_times)
        self.assertTrue(mock_create_single_process_and_execute_task.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.get_files_to_collect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.multitasking."
           "create_single_process_and_execute_task")
    def test_get_list_of_files_from_fls__is_successful(self, mock_create_single_process_and_execute_task, _):
        files = ["blah1", "blah2"]
        self.profile.data_type_file_id_dict = {data_type: 0 for data_type in self.profile.DATA_TYPES}
        mock_create_single_process_and_execute_task.return_value = files, {}
        self.assertEqual(files, self.profile.get_list_of_files_from_fls(self.fls, self.collection_times))
        self.assertTrue(mock_create_single_process_and_execute_task.called)

    #  any_sftp_processes_still_running test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_any_sftp_processes_still_running__returns_true_if_processes_still_running(self, mock_run_cmd_on_ms, *_):
        mock_run_cmd_on_ms.return_value = Mock(stdout="0 1 1 1\n")
        self.assertTrue(
            pm_fls_nbi_profile.any_sftp_processes_still_running("1", self.profile, self.user.username, 1234))
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_any_sftp_processes_still_running__returns_false_if_no_processes_still_running(
            self, mock_run_cmd_on_ms, *_):
        mock_run_cmd_on_ms.return_value = Mock(stdout="1 1 1 1\n")
        self.assertFalse(
            pm_fls_nbi_profile.any_sftp_processes_still_running("1", self.profile, self.user.username, 1234))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms", side_effect=Exception)
    def test_any_sftp_processes_still_running__raises_environerror_if_problem_occurs_checking_pids(self, *_):
        self.assertRaises(EnvironError,
                          pm_fls_nbi_profile.any_sftp_processes_still_running, 1, self.profile, self.user.username,
                          1234)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_local_cmd", side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.run_cmd_on_ms")
    def test_any_sftp_processes_still_running__raises_environerror_if_problem_occurs_checking_pids_if_not_physical(
            self, *_):
        self.assertRaises(EnvironError,
                          pm_fls_nbi_profile.any_sftp_processes_still_running, 1, self.profile, self.user.username,
                          1234)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils.lib.mutexer.mutex")
    @patch("enmutils_int.lib.pm_nbi.Fls.create_sftp_batch_files")
    def test_create_sftp_batch_files_on_server__is_successful(self, mock_create_sftp_batch_files, *_):
        files_to_collect = ["file1, file2, file3"]

        pm_nbi_batch_filename_prefix = (self.profile.PM_NBI_SFTP_BATCH_FILENAME.format(username=self.user.username) +
                                        "{:02d}")
        self.profile.create_sftp_batch_files_on_server(self.fls, files_to_collect)
        mock_create_sftp_batch_files.assert_called_with(
            data=files_to_collect,
            pm_nbi_dir=self.profile.PM_NBI_FETCHED_PM_FILES_DIR.format(username=self.fls.user.username),
            pm_nbi_batch_filename_prefix=pm_nbi_batch_filename_prefix,
            num_of_sftp_batch_files=self.profile.N_SFTP_THREADS, shuffle_data=True)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.Fls.create_sftp_batch_files")
    def test_create_sftp_batch_files_on_server__raises_EnvironError_if_cannot_create_sftp_batch_files(self, *_):
        files_to_collect = ["file1, file2, file3"]
        self.fls.create_sftp_batch_files.side_effect = Exception

        self.assertRaises(EnvironError, self.profile.create_sftp_batch_files_on_server, self.fls, files_to_collect)

    # log_results_of_nbi_transfer tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.mutexer.mutex")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    def test_log_results_of_nbi_transfer__is_successful(self, mock_logger, *_):
        nbi_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_file_count"] = 11200
        fls_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_fls_file_count"] = nbi_file_count
        results_identifier_text = "NBI File Transfer Results for user {0}:-".format(self.user.username)

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])
        time_taken_mins, time_taken_secs = divmod(time.time() - self.collection_times['start_time_of_iteration'], 60)

        success = "True"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FLS_FILE_COUNT: {3}, TRANSFERRED_FILE_COUNT: {4}, MISSED_FILE_COUNT: 0, "
                                "TIME_TAKEN: {5:02.0f}:{6:02.0f} mins:secs, SUCCESS: {7}".format(self.collection_times["start"],
                                                                                                 self.collection_times["end"],
                                                                                                 started_at_time, fls_file_count,
                                                                                                 fls_file_count, time_taken_mins,
                                                                                                 time_taken_secs, success))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_transfer(True, self.collection_times, self.user.username)
        mock_logger.assert_called_with(info_to_be_logged)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.mutexer.mutex")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    def test_log_results_of_nbi_transfer__is_unsuccessful_without_missed_file_count(self, mock_logger, *_):
        nbi_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_file_count"] = 0
        fls_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_fls_file_count"] = 999
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch1": 0}
        missed_count = fls_file_count - nbi_file_count

        results_identifier_text = "NBI File Transfer Results for user {0}:-".format(self.user.username)
        extra_text = "Note: Failures occurred - Check profile log for more details, "

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])
        time_taken_mins, time_taken_secs = divmod(time.time() - self.collection_times['start_time_of_iteration'], 60)
        success = "False"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FLS_FILE_COUNT: {3}, TRANSFERRED_FILE_COUNT: {4}, MISSED_FILE_COUNT: {5}, "
                                "TIME_TAKEN: {6:02.0f}:{7:02.0f} mins:secs, {9}SUCCESS: {8}"
                                .format(self.collection_times["start"], self.collection_times["end"],
                                        started_at_time, fls_file_count, nbi_file_count,
                                        missed_count, time_taken_mins, time_taken_secs, success, extra_text))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_transfer(False, self.collection_times, self.user.username)
        mock_logger.assert_called_with(info_to_be_logged)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.mutexer.mutex")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    def test_log_results_of_nbi_transfer__is_unsuccessful_with_missed_file_count(self, mock_logger, *_):
        nbi_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_file_count"] = 0
        fls_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_fls_file_count"] = 999
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch1": 999}
        missed_count = fls_file_count - nbi_file_count

        results_identifier_text = "NBI File Transfer Results for user {0}:-".format(self.user.username)
        extra_text = "Note: Failures occurred - Check profile log for more details, "

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])
        time_taken_mins, time_taken_secs = divmod(time.time() - self.collection_times['start_time_of_iteration'], 60)
        success = "False"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FLS_FILE_COUNT: {3}, TRANSFERRED_FILE_COUNT: {4}, MISSED_FILE_COUNT: {5}, "
                                "TIME_TAKEN: {6:02.0f}:{7:02.0f} mins:secs, {9}SUCCESS: {8}"
                                .format(self.collection_times["start"], self.collection_times["end"],
                                        started_at_time, fls_file_count, nbi_file_count,
                                        missed_count, time_taken_mins, time_taken_secs, success, extra_text))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_transfer(False, self.collection_times, self.user.username)
        mock_logger.assert_called_with(info_to_be_logged)

    # set_collection_times tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.mutexer.mutex")
    def test_set_collection_times__returned_dict_contains_correct_elements(self, *_):
        times = self.profile.set_collection_times(self.fls.user.username)

        self.assertEqual(len(times), 5)
        self.assertTrue("start_time_of_iteration" in times.keys())
        self.assertTrue("start" in times.keys())
        self.assertTrue("end" in times.keys())
        self.assertTrue("time_range" in times.keys())
        self.assertTrue("rop_interval" in times.keys())

        start_mins = int(times["start"].split(":")[1])
        end_mins = int(times["end"].split(":")[1])

        rop_times = [0, 15, 30, 45]
        self.assertIn(start_mins, rop_times)
        self.assertIn(end_mins, rop_times)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.mutexer.mutex")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.daylight", 0)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.time")
    def test_set_collection_times__is_successful_when_dst_not_in_use(
            self, mock_time, mock_datetime, *_):
        current_local_time = datetime(2018, 1, 1, 1, 5, 0, 0)  # DST not in use as time.daylight = 0
        expected_start_time_of_rop = "2018-01-01T00:45:00"
        expected_end_time_of_rop = "2018-01-01T01:00:00"

        mock_time.return_value = self.get_seconds_since_epoch(self.tz.localize(current_local_time))
        mock_datetime.fromtimestamp.return_value = current_local_time
        times = self.profile.set_collection_times(self.fls.user.username)
        self.assertEqual(times["start"], expected_start_time_of_rop)
        self.assertEqual(times["end"], expected_end_time_of_rop)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.daylight")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.altzone", -60 * 60)  # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.timezone", 0)  # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_0_if_dst_inactive_for_both_iteration_start_time_and_rop_time(
            self, mock_localtime, *_):
        # Iteration start time is 05:07 Jan 1st, and DST is inactive for that time as well as for ROP time

        # Start time of ROP = iteration_start_time (5:07:00)
        #                       - current_rop_offset (7m, 0s)
        #                       - timedelta_for_rop_from_iteration_start_time (45m)
        #                       - start_time_dst_offset (0m)
        # This corresponds to ROP to be fetched with start time of 04:15

        iteration_start_time = datetime(2018, 1, 1, 5, 7, 0, 0)
        timedelta_for_rop_from_iteration_start_time = timedelta(minutes=45)

        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_rop_start_time = self.tz.localize(iteration_start_time -
                                                          timedelta_for_rop_from_iteration_start_time).timetuple()
        mock_localtime.side_effect = [time_struct_for_iteration_start_time, time_struct_for_rop_start_time]

        start_time_dst_offset = self.profile.calculate_dst_offset_for_fetched_rop(9999)
        self.assertEqual(start_time_dst_offset, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.daylight")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.altzone", -60 * 60)  # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.timezone", 0)  # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_0_if_dst_active_for_both_iteration_start_time_and_rop_time(
            self, mock_localtime, *_):
        # Iteration start time is 05:07 Jun 1st, and DST active for that time as well as for ROP time

        # Start time of ROP = iteration_start_time (5:07:00)
        #                       - current_rop_offset (7m, 0s)
        #                       - timedelta_for_rop_from_iteration_start_time (45m)
        #                       - start_time_dst_offset (0m)
        # This corresponds to ROP to be fetched with start time of 04:15

        iteration_start_time = datetime(2018, 6, 1, 5, 7, 0, 0)
        timedelta_for_rop_from_iteration_start_time = timedelta(minutes=45)

        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_rop_start_time = self.tz.localize(iteration_start_time -
                                                          timedelta_for_rop_from_iteration_start_time).timetuple()
        mock_localtime.side_effect = [time_struct_for_iteration_start_time, time_struct_for_rop_start_time]

        start_time_dst_offset = self.profile.calculate_dst_offset_for_fetched_rop(9999)
        self.assertEqual(start_time_dst_offset, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.daylight")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.altzone", -60 * 60)  # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.timezone", 0)  # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_plus_60_if_dst_active_for_current_time_but_inactive_for_rop(
            self, mock_localtime, *_):
        # DST starts in Dublin at 25/3/2018 02:00 so picking iteration start time of 02:07:00 on that same day

        # Start time of ROP = iteration_start_time (2:07:00)
        #                       - current_rop_offset (7m, 0s)
        #                       - timedelta_for_rop_from_iteration_start_time (45m)
        #                       - start_time_dst_offset (+60m)
        # This corresponds to ROP to be fetched with start time of 00:15

        iteration_start_time = datetime(2018, 3, 25, 2, 7, 0, 0)
        timedelta_for_rop_from_iteration_start_time = timedelta(minutes=45)

        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_rop_start_time = self.tz.localize(
            (iteration_start_time - timedelta_for_rop_from_iteration_start_time)).timetuple()
        mock_localtime.side_effect = [time_struct_for_iteration_start_time, time_struct_for_rop_start_time]

        start_time_dst_offset = self.profile.calculate_dst_offset_for_fetched_rop(9999)
        self.assertEqual(start_time_dst_offset, 60)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.daylight")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.altzone", -60 * 60)  # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.timezone", 0)  # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_minus_60_if_dst_inactive_for_current_time_but_active_for_rop(
            self, mock_localtime, *_):
        # DST ends in Dublin at 28/10/2018 01:00 so picking iteration start time of 01:07:00 on that same day,

        # Start time of ROP = iteration_start_time (1:07:00)
        #                       - current_rop_offset (7m, 0s)
        #                       - timedelta_for_rop_from_iteration_start_time (45m)
        #                       - start_time_dst_offset (-60m)
        # This corresponds to ROP to be fetched with start time of 01:15

        iteration_start_time = datetime(2018, 10, 28, 1, 7, 0, 0)
        timedelta_for_rop_from_iteration_start_time = timedelta(minutes=45)

        time_struct_for_iteration_start_time = self.tz.localize(iteration_start_time).timetuple()
        time_struct_for_rop_start_time = self.tz.localize(
            (iteration_start_time - timedelta_for_rop_from_iteration_start_time)).timetuple()
        mock_localtime.side_effect = [time_struct_for_iteration_start_time, time_struct_for_rop_start_time]

        start_time_dst_offset = self.profile.calculate_dst_offset_for_fetched_rop(9999)
        self.assertEqual(start_time_dst_offset, -60)

    # execute_flow tests
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "check_and_add_new_datatypes_to_datatype_fileid_dict")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=["PM_STATISTICAL",
                                                                                      "PM_UETR",
                                                                                      "PM_CTUM",
                                                                                      "TOPOLOGY_TCIM",
                                                                                      "TOPOLOGY_TRANSPORT"])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_enm_on_cloud_native",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.get_ms_host", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.keep_running",
           side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.state", return_value="RUNNING")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.perform_fls_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "initiate_profile_and_environment")
    def test_execute_flow__is_successful(self, mock_initiate_profile_and_environment, mock_perform_fls_nbi_operations,
                                         mock_sleep, mock_add_error_as_exception, *_):
        fls_list = [self.fls, self.fls]
        mock_initiate_profile_and_environment.return_value = fls_list
        self.profile.execute_flow()
        mock_perform_fls_nbi_operations.assert_called_with(fls_list)
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertEqual(2, mock_sleep.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "check_and_add_new_datatypes_to_datatype_fileid_dict")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=["PM_STATISTICAL",
                                                                                      "PM_UETR",
                                                                                      "PM_CTUM",
                                                                                      "TOPOLOGY_TCIM",
                                                                                      "TOPOLOGY_TRANSPORT"])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_enm_on_cloud_native",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.get_ms_host", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.state", return_value="RUNNING")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.keep_running")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.perform_fls_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "initiate_profile_and_environment")
    def test_execute_flow__adds_error_if_initiate_profile_and_environment_throws_exception(
            self, mock_initiate_profile_and_environment, mock_perform_fls_nbi_operations,
            mock_sleep, mock_add_error_as_exception, mock_keep_running, *_):
        mock_initiate_profile_and_environment.side_effect = Exception("something is wrong")
        self.profile.execute_flow()
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertTrue(mock_initiate_profile_and_environment.called)
        self.assertFalse(mock_perform_fls_nbi_operations.called)
        self.assertFalse(mock_keep_running.called)
        self.assertEqual(0, mock_sleep.call_count)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "check_and_add_new_datatypes_to_datatype_fileid_dict")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile."
           "get_matched_supported_datatypes_with_configured_datatypes", side_effect=[EnvironError("Error")])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_host_physical_deployment",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.is_enm_on_cloud_native",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.cache.get_ms_host", return_value=True)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.state", return_value="RUNNING")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.perform_fls_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "initiate_profile_and_environment")
    def test_execute_flow__if_matched_data_types_not_found(self, mock_initiate_profile_and_environment,
                                                           mock_perform_fls_nbi_operations,
                                                           mock_sleep, mock_add_error_as_exception, *_):
        fls_list = [self.fls, self.fls]
        mock_initiate_profile_and_environment.return_value = fls_list
        self.profile.execute_flow()
        self.assertTrue(mock_perform_fls_nbi_operations.call_cont, 0)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertEqual(0, mock_sleep.call_count)

    # perform_fls_nbi_operations test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "get_active_scripting_service_ip_list", side_effect=EnvironError("Error"))
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "enable_passwordless_login_for_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.perform_sftp_transfer_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.pexpect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_fls_nbi_operations__adds_error_get_active_scripting_service_ip_list_throws_exception(
            self, mock_add_exception, mock_pexpect, *_):
        child = mock_pexpect.spawn()
        child.expect.return_value = "root@"
        self.profile.is_physical = False
        fls_tuple_list = [(self.fls, 0), (self.fls, 20)]
        self.profile.perform_fls_nbi_operations(fls_tuple_list)
        self.assertEqual(mock_add_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "get_active_scripting_service_ip_list", return_value=["ip1", "ip2"])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.pexpect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "enable_passwordless_login_for_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.perform_sftp_transfer_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_fls_nbi_operations__is_successful(self, mock_add_exception,
                                                       mock_perform_sftp_transfer_tasks,
                                                       mock_enable_pwdless_login_for_users, mock_pexpect, _):
        self.profile.is_physical = True
        child = mock_pexpect.spawn()
        child.expect.return_value = "root@"
        fls_tuple_list = [(self.fls, 0)]
        self.profile.perform_fls_nbi_operations(fls_tuple_list)
        self.assertEqual(1, mock_perform_sftp_transfer_tasks.call_count)
        self.assertEqual(1, mock_enable_pwdless_login_for_users.call_count)
        self.assertEqual(mock_add_exception.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.pexpect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "get_active_scripting_service_ip_list", return_value=["ip1", "ip2"])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "enable_passwordless_login_for_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.perform_sftp_transfer_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_fls_nbi_operations__on_cemm_cloud(self, mock_add_exception,
                                                       mock_perform_sftp_transfer_tasks,
                                                       mock_enable_pwdless_login_for_users, *_):
        self.profile.is_physical = False
        fls_tuple_list = [(self.fls, 0)]
        self.profile.perform_fls_nbi_operations(fls_tuple_list)
        mock_perform_sftp_transfer_tasks.assert_called_with(fls_tuple_list[0], self.profile)
        mock_enable_pwdless_login_for_users.asser_called_with(fls_tuple_list, ["ip1", "ip2"])
        self.assertEqual(mock_add_exception.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "get_active_scripting_service_ip_list", return_value=["ip1", "ip2"])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.pexpect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "enable_passwordless_login_for_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.perform_sftp_transfer_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_fls_nbi_operations__if_scripting_vm_true(self, mock_add_exception,
                                                              mock_perform_sftp_transfer_tasks,
                                                              mock_enable_pwdless_login_for_users, mock_pexpect, _):
        self.profile.is_physical = False
        child = mock_pexpect.spawn()
        child.expect.return_value = "root@"
        fls_tuple_list = [(self.fls, 0)]
        self.profile.perform_fls_nbi_operations(fls_tuple_list)
        mock_perform_sftp_transfer_tasks.assert_called_with(fls_tuple_list[0], self.profile)
        mock_enable_pwdless_login_for_users.asser_called_with(fls_tuple_list, ["ip1", "ip2"], is_scripting_vm=True)
        self.assertEqual(mock_add_exception.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "get_active_scripting_service_ip_list", return_value=["ip1", "ip2"])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.pexpect")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile."
           "enable_passwordless_login_for_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.perform_sftp_transfer_tasks")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_fls_nbi_operations__if_login_failed_to_lms(self, mock_add_exception,
                                                                mock_perform_sftp_transfer_tasks,
                                                                mock_enable_pwdless_login_for_users, mock_pexpect, _):
        self.profile.is_physical = True
        child = mock_pexpect.spawn()
        child.expect.side_effect = Exception("Error")
        fls_tuple_list = [(self.fls, 0)]
        self.profile.perform_fls_nbi_operations(fls_tuple_list)
        self.assertEqual(0, mock_perform_sftp_transfer_tasks.call_count)
        self.assertEqual(0, mock_enable_pwdless_login_for_users.call_count)
        self.assertEqual(mock_add_exception.call_count, 1)

    # perform_sftp_transfer_tasks test cases
    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_pm_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.transfer_pmic_files_to_nbi")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.set_collection_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_sftp_transfer_tasks__is_successful(
            self, mock_add_error_as_exception, mock_set_collection_times, mock_transfer_pmic_files, *_):
        mock_transfer_pmic_files.return_value = True
        mock_set_collection_times.return_value = self.collection_times
        pm_fls_nbi_profile.perform_sftp_transfer_tasks((self.fls, 0), self.profile)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_pm_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.transfer_pmic_files_to_nbi")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.set_collection_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    def test_perform_sftp_transfer_tasks__adds_error_if_transfer_pmic_files_to_nbi_result_was_false(self, mock_add_error_as_exception,
                                                                                                    mock_set_collection_times,
                                                                                                    mock_transfer_pmic_files, *_):
        mock_transfer_pmic_files.return_value = False
        mock_set_collection_times.return_value = self.collection_times
        pm_fls_nbi_profile.perform_sftp_transfer_tasks((self.fls, 0), self.profile)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile.Profile.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.transfer_pmic_files_to_nbi",
           side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.check_pm_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.set_collection_times")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.log_results_of_nbi_transfer")
    def test_perform_sftp_transfer_tasks__adds_error_if_transfer_pmic_files_to_nbi_result_throws_exception(
            self, mock_log_results_of_nbi_transfer, mock_add_error_as_exception, mock_set_collection_times, *_):
        mock_set_collection_times.return_value = self.collection_times
        pm_fls_nbi_profile.perform_sftp_transfer_tasks((self.fls, 0), self.profile)
        self.assertFalse(mock_log_results_of_nbi_transfer.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.execute_flow")
    def test_run__in_pm26_is_successful(self, _):
        pm_26 = PM_26()
        pm_26.run()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.execute_flow")
    def test_run__in_pm45_is_successful(self, _):
        pm_45 = PM_45()
        pm_45.run()

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.PmFlsNbiProfile.execute_flow")
    def test_run__in_pm28_is_successful(self, _):
        pm_28 = PM_28()
        pm_28.run()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.ConnectionPoolManager.__init__',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.ConnectionPoolManager.return_connection')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.ConnectionPoolManager.get_connection')
    def test_are_ssh_credentials_valid__success(self, mock_get, mock_return, _):
        self.assertTrue(self.profile.are_ssh_credentials_valid("host", "user", "pass"))
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_return.call_count)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.ConnectionPoolManager.__init__',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.ConnectionPoolManager.return_connection')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.shell.ConnectionPoolManager.get_connection')
    def test_are_ssh_credentials_valid__get_connection_fails(self, mock_get, mock_return, _):
        mock_get.side_effect = Exception("Error")
        self.assertFalse(self.profile.are_ssh_credentials_valid("host", "user", "pass"))
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_return.call_count)

    # check_and_add_new_datatypes_to_datatype_fileid_dict test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*',
                                                                                      'PM_UETRACE'])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.datetime.datetime")
    def test_check_and_add_new_datatypes_to_datatype_fileid_dict__is_successful(self, mock_datetime, mock_debug_log, _):
        self.profile.data_type_file_id_dict = {'TOPOLOGY_*': [0, None], 'PM_STATISTICAL': [2, None],
                                               'PM_UETR': [0, None]}
        mock_datetime.now.return_value = datetime(2024, 02, 12, 0, 0, 0)
        self.profile.check_and_add_new_datatypes_to_datatype_fileid_dict()
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.datetime.datetime")
    def test_check_and_add_new_datatypes_to_datatype_fileid_dict__if_no_datatype_found(self, mock_datetime,
                                                                                       mock_debug_log, _):
        self.profile.data_type_file_id_dict = {'TOPOLOGY_*': [0, None], 'PM_STATISTICAL': [2, None],
                                               'PM_UETR': [0, None]}
        mock_datetime.now.return_value = datetime(2024, 02, 12, 0, 0, 0)
        self.profile.check_and_add_new_datatypes_to_datatype_fileid_dict()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile.datetime.datetime")
    def test_check_and_add_new_datatypes_to_datatype_fileid_dict__if_time_is_different(self, mock_datetime,
                                                                                       mock_debug_log, _):
        self.profile.data_type_file_id_dict = {'TOPOLOGY_*': [0, None], 'PM_STATISTICAL': [2, None],
                                               'PM_UETR': [0, None]}
        mock_datetime.now.return_value = datetime(2024, 02, 12, 4, 0, 0)
        self.profile.check_and_add_new_datatypes_to_datatype_fileid_dict()
        self.assertEqual(mock_debug_log.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
