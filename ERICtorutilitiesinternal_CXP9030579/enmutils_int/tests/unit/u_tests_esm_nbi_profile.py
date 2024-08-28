#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from mock import patch, Mock, PropertyMock, call
from pytz import timezone, utc

from enmutils.lib.exceptions import EnvironError, TimeOutError
from enmutils_int.lib.profile_flows.esm_nbi_flows import esm_nbi_profile
from enmutils_int.lib.workload.esm_nbi_01 import ESM_NBI_01

from testslib import unit_test_utils


class ESMNBI01ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")
        self.profile = esm_nbi_profile.EsmNbiProfile()
        self.profile.NAME = "ESM_NBI_01"
        self.profile.NUM_USERS = 1
        self.profile.USER_ROLES = ["ADMINISTRATOR"]
        self.profile.SCHEDULED_TIMES_STRINGS = ["{0}:{1}:00".format(hour, minute) for hour in range(00, 24)
                                                for minute in range(5, 60, 15)]
        self.profile.ROP_INTERVAL = 15
        self.profile.nbi_transfer_stats[self.user.username] = {"failed_timestamps": 0}
        self.profile.users = [self.user]
        self.profile.enm_url = None
        self.profile.NEW_REMOTE_WRITE_URL = "http://remotewriter-nbi-profile:1234/receive"
        start_time = "2022-09-22T15:30:00"
        end_time = "2022-09-22T15:45:00"
        self.time_now = 1662375189.478916
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

    # calculate_dst_offset_for_fetched_rop test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.daylight", return_value=0)
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_0_if_dst_inactive_for_both_iteration_start_time_and_rop_time(
            self, mock_localtime, mock_debug_log, *_):
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
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.daylight")
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_0_if_dst_active_for_both_iteration_start_time_and_rop_time(
            self, mock_localtime, mock_debug_log, *_):
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
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.daylight")
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_plus_60_if_dst_active_for_current_time_but_inactive_for_rop(
            self, mock_localtime, mock_debug_log, *_):
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
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.daylight")
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.localtime")
    def test_calculate_dst_offset_for_fetched_rop__returns_minus_60_if_dst_inactive_for_current_time_but_active_for_rop(
            self, mock_localtime, mock_debug_log, *_):
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
        self.assertEqual(mock_debug_log.call_count, 1)

    # set_collection_times tests

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_set_collection_times__returned_dict_contains_correct_elements(self, *_):
        times = self.profile.set_collection_times()
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

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.daylight", 0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.time")
    def test_set_collection_times__is_successful_when_dst_not_in_use(
            self, mock_time, mock_datetime, *_):
        current_local_time = datetime(2018, 1, 1, 1, 5, 0, 0)  # DST not in use as time.daylight = 0
        expected_start_time_of_rop = "2018-01-01T00:45:00"
        expected_end_time_of_rop = "2018-01-01T01:00:00"

        mock_time.return_value = self.get_seconds_since_epoch(self.tz.localize(current_local_time))
        mock_datetime.fromtimestamp.return_value = current_local_time
        times = self.profile.set_collection_times()
        self.assertEqual(times["start"], expected_start_time_of_rop)
        self.assertEqual(times["end"], expected_end_time_of_rop)

    # log_results_of_nbi_transfer tests

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_log_results_of_nbi_metrics_received__is_successful(self, mock_logger, _):
        self.profile.nbi_transfer_stats[self.user.username] = {"failed_timestamps": 0}
        metric_count_text = self.profile.nbi_transfer_stats[self.user.username]["failed_timestamps"]
        results_identifier_text = "NBI Metrics received Results for user {0}:-".format(self.user.username)

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])
        success = "True"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FAILED_TIMESTAMPS: {3}, SUCCESS: {4}"
                                .format(self.collection_times["start"], self.collection_times["end"], started_at_time,
                                        metric_count_text, success))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_metrics_received(self.collection_times)
        mock_logger.assert_called_with(info_to_be_logged)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_log_results_of_nbi_metrics_received__is_unsuccessful(self, mock_logger, _):
        self.profile.nbi_transfer_stats[self.user.username] = {"failed_timestamps": [('1', '2023-05-12 06:59:23'),
                                                                                     ('1', '2023-05-12 07:00:23'),
                                                                                     ('1', '2023-05-12 07:01:23'),
                                                                                     ('1', '2023-05-12 07:02:23'),
                                                                                     ('1', '2023-05-12 07:03:23'),
                                                                                     ('1', '2023-05-12 07:04:23'),
                                                                                     ('1', '2023-05-12 07:05:23'),
                                                                                     ('1', '2023-05-12 07:06:23'),
                                                                                     ('1', '2023-05-12 07:07:23'),
                                                                                     ('1', '2023-05-12 07:08:23'),
                                                                                     ('1', '2023-05-12 07:09:23')]}
        metric_count_text = self.profile.nbi_transfer_stats[self.user.username]["failed_timestamps"]
        results_identifier_text = "NBI Metrics received Results for user {0}:-".format(self.user.username)
        extra_text = "Note: Prometheus retried number of samples per second to NBI at their respective timestamps "

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])

        success = "False"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FAILED_TIMESTAMPS: {3}, {4}SUCCESS: {5}"
                                .format(self.collection_times["start"], self.collection_times["end"],
                                        started_at_time, metric_count_text, extra_text, success))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)

        self.profile.log_results_of_nbi_metrics_received(self.collection_times)
        mock_logger.assert_called_with(info_to_be_logged)

    # create_pod_on_cn test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    def test_create_pod_on_cn__is_successful(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=True, stdout="success")
        self.assertEqual(True, esm_nbi_profile.create_pod_on_cn("cenm168", "path", "remotewriter-nbi-profile"))
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    def test_create_pod_on_cn__raises_environ_error(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, esm_nbi_profile.create_pod_on_cn, "cenm168", "path", "remotewriter-nbi-profile")
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    # delete_pod_on_cn test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    def test_delete_pod_on_cn__is_successful(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=True, stdout="success")
        self.assertEqual(True, esm_nbi_profile.delete_pod_on_cn("cenm168", "path", "remotewriter-nbi-profile"))
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    def test_delete_pod_on_cn__raises_environ_error(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, esm_nbi_profile.delete_pod_on_cn, "cenm168", "path", "remotewriter-nbi-profile")
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    # verify_metrics_received_into_pod test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_verify_metrics_received_into_pod___add_error_as_exception(self, mock_debug_log, mock_run_cmd, mock_add_error, *_):
        mock_run_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, self.profile.verify_metrics_received_into_pod, "cenm168",
                          self.profile.NEW_REMOTE_WRITE_URL)
        self.assertEqual(mock_run_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertTrue(call(EnvironError in mock_add_error.mock_calls))

    # check_configmap_exists_on_cn test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.run_local_cmd")
    def test_check_configmap_exists_on_cn__is_successful(self, mock_local_cmd, mock_cmd):
        mock_local_cmd.return_value = Mock(ok=True)
        self.assertEqual(True, esm_nbi_profile.check_configmap_exists_on_cn("cenm618"))
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.run_local_cmd")
    def test_check_configmap_exists_on_cn__is_unsuccessful(self, mock_local_cmd, mock_cmd):
        mock_local_cmd.return_value = Mock(ok=False)
        self.assertRaises(EnvironError, esm_nbi_profile.check_configmap_exists_on_cn, "cenm618")
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 1)

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "verify_metrics_received_into_pod")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.partial")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "update_remote_write_url_in_configmap")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_configmap_exists_on_cn",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "verify_remote_write_url_in_configmap")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "perform_esm_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.create_users")
    def test_execute_flow__is_successful(self, mock_create_users, mock_perform_esm_nbi_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_perform_esm_nbi_operations.call_count, 1)

    # verify_metrics_received_into_pod test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_verify_metrics_received_into_pod___add_error(self, mock_debug_log, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value = Mock(rc=0,
                                               stdout="1 @[1683626633]\n1 @[1683626693]\n0 @[1683626753]\n"
                                                      "1 @[1683626813]", ok=True)
        esm_nbi_profile.EsmNbiProfile.verify_metrics_received_into_pod(self.profile, "cenm168",
                                                                       self.profile.NEW_REMOTE_WRITE_URL)
        self.assertEqual(mock_run_local_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_verify_metrics_received_into_pod___is_successful(self, mock_debug_log, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value = Mock(rc=0,
                                               stdout="0 @[1683626633]\n0 @[1683626693]\n0 @[1683626753]\n"
                                                      "0 @[1683626813]", ok=True)
        esm_nbi_profile.EsmNbiProfile.verify_metrics_received_into_pod(self.profile, "cenm168",
                                                                       "http://remotewriter-nbi-profile:1234/receive")
        self.assertEqual(mock_run_local_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.partial")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.update_remote_write_url_in_configmap")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_configmap_exists_on_cn",
           side_effect=EnvironError)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.verify_remote_write_url_in_configmap")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "perform_esm_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.keep_running")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.create_profile_users")
    def test_execute_flow__add_error_exception(self, mock_create_users, mock_keep_running, mock_perform, mock_add_error,
                                               *_):
        mock_create_users.return_value = [Mock(username="test")]
        mock_keep_running.side_effect = [True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_perform.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_configmap_exists_on_cn",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.create_users")
    def test_execute_flow__if_configmap_do_not_exists_on_cn(self, mock_create_users,
                                                            mock_perform_esm_nbi_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_esm_nbi_operations.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_configmap_exists_on_cn",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.create_pod_on_cn", return_value=False)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.create_users")
    def test_execute_flow__if_create_pod_on_cn_is_failed(self, mock_create_users, mock_perform_esm_nbi_operations, *_):
        mock_create_users.return_value = [Mock(username="testuser")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_esm_nbi_operations.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_configmap_exists_on_cn",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.check_pod_is_running",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.create_users")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "perform_esm_nbi_operations")
    def test_execute_flow__if_remotewriternbiprofile_is_not_running(self, mock_perform_esm_nbi_operations,
                                                                    mock_create_users, *_):
        mock_create_users.return_value = [Mock(username="test1")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_esm_nbi_operations.call_count, 0)

    # perform_esm_nbi_operations test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "set_collection_times", return_value={"end": "2022-09-22T15:45:00"})
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "log_results_of_nbi_metrics_received")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.verify_remote_write_url_in_configmap")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.verify_metrics_received_into_pod")
    def test_perform_esm_nbi_operations__is_successful(self, mock_debug_log, *_):
        self.profile.perform_esm_nbi_operations()
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "set_collection_times")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "verify_metrics_received_into_pod", side_effect=EnvironError("Error"))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "verify_remote_write_url_in_configmap")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config")
    def test_perform_perform_esm_nbi_operations__add_error_as_exception(self, mock_add_error, *_):
        self.profile.perform_esm_nbi_operations()
        self.assertEqual(mock_add_error.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "set_collection_times")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "log_results_of_nbi_metrics_received")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "verify_metrics_received_into_pod")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(data={'prometheus.yml': "remote_write:\n  - url: http://remotewriter-nbi-profile:1234/receive\n    remote_timeout: 30s\n"})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile."
           "verify_remote_write_url_in_configmap", return_value=False)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    def test_perform_perform_esm_nbi_operations__remote_write_url_not_in_configmap(self, mock_debug_log, *_):
        self.profile.perform_esm_nbi_operations()
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(data={"prometheus.yml": {"remote_write": [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]}})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml.safe_load",
           return_value={'remote_write': [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]})
    def test_verify_remote_write_url_in_configmap__returns_true(self, *_):
        self.profile.verify_remote_write_url_in_configmap("cenm168", "eric-pm-server")

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(data={"prometheus.yml": {"remote_write": [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]}})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml.safe_load",
           return_value={'remote_write': [{'url': 'http://reewriter-nbi-profile:134564/receive'}]})
    def test_verify_remote_write_url_in_configmap__returns_false(self, *_):
        self.profile.verify_remote_write_url_in_configmap("cenm168", "eric-pm-server")

    # test_get_prometheus_config test cases
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.config")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.client")
    def test_get_prometheus_config__is_successful(self, *_):
        self.assertEqual(2, len(self.profile.get_prometheus_config("testnamespace", "test")))

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(
               data={'prometheus.yml': "remote_write:\n  - url: http://remotewriter-nbi-profile:1234/receive\n    remote_timeout: 30s\n"})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml.safe_load",
           return_value={'remote_write': [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]})
    def test_update_remote_write_url_in_configmap_action_add(self, *_):
        self.profile.READ_TIMEOUT = "30"
        self.profile.NEW_REMOTE_WRITE_NAME = "esm_nbi_01"
        self.profile.update_remote_write_url_in_configmap("cenm168", "eric-pm-server", "add")

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(
               data={
                   'prometheus.yml': "remote_writer:\n  - url: http://remotewriter-nbi-profile:1234/receive\n    remote_timeout: 30s\n"})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml.safe_load",
           return_value={'remote_write': [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]})
    def test_update_remote_write_url_in_configmap_action_add_remote_write(self, *_):
        self.profile.READ_TIMEOUT = "30"
        self.profile.NEW_REMOTE_WRITE_NAME = "esm_nbi_01"
        self.profile.update_remote_write_url_in_configmap("cenm167", "eric-pm-server", "add")

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(
               data={'prometheus.yml': "remote_write:\n  - url: http://remotewriter-nbi-profile:1234/receive\n    remote_timeout: 30s\n"})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml.safe_load",
           return_value={'remote_write': [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]})
    def test_update_remote_write_url_in_configmap_action_remove(self, *_):
        self.profile.READ_TIMEOUT = "30"
        self.profile.NEW_REMOTE_WRITE_NAME = "esm_nbi_01"
        self.profile.update_remote_write_url_in_configmap("cenm168", "eric-pm-server", "remove")

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.get_prometheus_config",
           return_value=(Mock(), Mock(
               data={'prometheus.yml': "remote_write:\n  - url: http://remotewriter-nbi-profile:1234/receive\n    remote_timeout: 30s\n"})))
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.yaml.safe_load",
           return_value={'remote_write': [{'url': 'http://remotewriter-nbi-profile:1234/receive'}]})
    def test_update_remote_write_url_in_configmap(self, *_):
        self.profile.READ_TIMEOUT = "30"
        self.profile.NEW_REMOTE_WRITE_NAME = "esm_nbi_01"
        self.profile.update_remote_write_url_in_configmap("cenm168", "eric-pm-server", "")

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.run_local_cmd")
    def test_check_pod_is_running__is_successful(self, mock_local_cmd, mock_cmd, mock_debug_log, mock_timedelta,
                                                 mock_datetime, *_):
        mock_local_cmd.side_effect = [Mock(stdout="Pending"), Mock(stdout="Pending"), Mock(stdout="Running")]
        time_now = datetime(2022, 9, 6, 9, 0, 0)
        expiry_time = datetime(2022, 9, 6, 9, 9, 2, 0)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        esm_nbi_profile.check_pod_is_running("path", "remotewriter-nbi-profile")
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_cmd.call_count, 3)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.Command")
    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.run_local_cmd")
    def test_check_pod_is_running__raises_timeout_error(self, mock_local_cmd, mock_cmd, mock_debug_log,
                                                        mock_timedelta, mock_datetime, *_):
        mock_local_cmd.side_effect = [Mock(stdout="Pending"), Mock(stdout="Pending"), Mock(stdout="Running")]
        time_now = datetime(2022, 9, 6, 9, 0, 0)
        expiry_time = datetime(2022, 9, 6, 9, 9, 2, 0)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = expiry_time - time_now
        self.assertRaises(TimeOutError, esm_nbi_profile.check_pod_is_running, "enmcc1", "remotewriter-nbi-profile")
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile.EsmNbiProfile.execute_flow")
    def test_run__in_remotewriternbiprofile_is_successful(self, mock_execute_flow):
        ESM_NBI_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
