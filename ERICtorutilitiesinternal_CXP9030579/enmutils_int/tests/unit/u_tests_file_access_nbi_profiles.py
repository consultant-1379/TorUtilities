#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from mock import patch, Mock, call, PropertyMock, mock_open
from pytz import timezone, utc
from enmutils.lib.exceptions import EnvironError, TimeOutError
from enmutils_int.lib.pm_nbi import Fls
from enmutils_int.lib.profile_flows.fan_flows import file_access_nbi_profiles
from enmutils_int.lib.workload.fan_11 import FAN_11
from enmutils_int.lib.workload.fan_12 import FAN_12
from enmutils_int.lib.workload.fan_13 import FAN_13
from enmutils_int.lib.workload.fan_14 import FAN_14
from testslib import unit_test_utils


class FAN01ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")
        self.fls = Fls(user=self.user)
        self.profile = file_access_nbi_profiles.FileAccessNbiProfile()
        self.profile.SERVICE_FORWARD_PORT = 6767
        self.profile.fan_pod_ip = ["fan-01"]
        self.profile.NAME = "FAN_01"
        self.profile.NUM_OF_CURL_PARALLEL_REQUESTS = 2
        self.profile.POD_CPU = "2000m"
        self.profile.POD_MEMORY = "1Gi"
        self.profile.NUM_USERS = 1
        self.profile.USER_ROLES = ["PM_NBI_Operator"]
        self.profile.SCHEDULED_TIMES_STRINGS = ["{0}:{1}:00".format(hour, minute) for hour in range(00, 24)
                                                for minute in range(5, 60, 15)]
        self.profile.DATA_TYPES = ["PM_STATISTICAL", "PM_CELLTRACE", "PM_CTUM"]
        self.profile.NUM_OF_BATCHES = 10
        self.profile.FILES_FETCH_TIME_IN_MINS = 15
        self.profile.ROP_INTERVAL = 15
        self.profile.active_scripting_service_ip_list = ["ip_a", "ip_b"]
        self.profile.DATA_TYPES_UPDATE_TIME = "00:00"

        self.profile.nbi_transfer_stats[self.user.username] = {"nbi_transfer_time": 0, "nbi_fls_file_count": 0,
                                                               "missed_file_count": {}}
        self.profile.data_type_file_id_dict = {self.user.username: {'PM_CELLTRACE': [0, None],
                                                                    'PM_STATISTICAL': [2, None],
                                                                    'PM_CTUM': [0, None]}}
        self.profile.users = [self.user]
        self.profile.fan01_pod_ip = ["ip"]
        self.profile.enm_url = None
        self.profile.FAN_NBI_BATCH_FILENAME = "/tmp/test"
        self.profile.rest_api_main_url = "http://localhost:5000"
        start_time = "2022-09-22T15:30:00"
        end_time = "2022-09-22T15:45:00"
        self.time_now = 1662375189.478916
        self.tz = timezone("Europe/Dublin")
        self.collection_times = {"start_time_of_iteration": self.time_now - 10,
                                 "start": start_time,
                                 "end": end_time,
                                 "time_range": (start_time, end_time),
                                 "rop_interval": self.profile.ROP_INTERVAL}
        self.fetch_files_api_success_response = {'total_time': '0.34 min', 'files': 12653,
                                                 'total_seconds': 20.489119052886963,
                                                 'data_types_dict': {u'PM_UETRACE_D': [0, ''],
                                                                     u'PM_EBSM_3GPP': [0, ''],
                                                                     u'PM_CELLTRACE_CUUP': [0, ''],
                                                                     u'PM_EBS': [0, ''],
                                                                     u'PM_STATISTICAL': [21126219,
                                                                                         '2022-12-06T09:22:06'],
                                                                     u'PM_EBM': [21126986, '2022-12-06T09:29:02'],
                                                                     u'PM_CELLTRACE': [21125386,
                                                                                       '2022-12-06T09:21:29'],
                                                                     u'PM_UETR': [21125328, '2022-12-06T09:21:14'],
                                                                     u'PM_CTUM': [21123590, '2022-12-06T09:21:04'],
                                                                     u'PM_STATISTICAL_12HOUR': [0, ''],
                                                                     u'PM_EBSN_D': [0, ''],
                                                                     u'PM_EBSN_CUCP': [0, ''],
                                                                     u'PM_STATISTICAL_1MIN': [21126946,
                                                                                              '2022-12-06T09:29:03'],
                                                                     u'PM_BSC_PERFORMANCE_EVENT_MONITORS': [0, ''],
                                                                     u'PM_CELLTRACE_CUCP': [0, ''],
                                                                     u'PM_EBSN_CUUP': [0, ''],
                                                                     u'PM_UETRACE': [21125975,
                                                                                     '2022-12-06T09:21:52'],
                                                                     u'PM_CELLTRACE_D': [0, ''],
                                                                     u'PM_GPEH': [21126286,
                                                                                  '2022-12-06T09:22:22'],
                                                                     u'PM_STATISTICAL_1HOUR': [0, ''],
                                                                     u'PM_BSC_RTT': [0, ''],
                                                                     u'PM_BSC_PERFORMANCE_EVENT_STATISTICS': [0, ''],
                                                                     u'PM_UETRACE_CUCP': [0, ''],
                                                                     u'PM_EBSM_ENIQ': [0, ''],
                                                                     u'PM_CELLTRAFFIC': [21124493,
                                                                                         '2022-12-06T09:21:14'],
                                                                     u'PM_BSC_PERFORMANCE_CTRL': [0, ''],
                                                                     u'PM_UETRACE_CUUP': [0, ''],
                                                                     u'PM_STATISTICAL_30MIN': [0, ''],
                                                                     u'PM_EBSL': [0, ''],
                                                                     u'PM_STATISTICAL_5MIN': [0, ''],
                                                                     u'PM_BSC_PERFORMANCE_EVENT_RAW': [0, ''],
                                                                     u'PM_STATISTICAL_24HOUR': [0, ''],
                                                                     u'PM_BSC_PERFORMANCE_EVENT': [0, ''],
                                                                     u'PM_CTR': [0, '']},
                                                 'file_locations': ['/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_00.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_01.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_03.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_04.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_05.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_06.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_07.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_08.txt',
                                                                    '/var/tmp/fan_nbi/administrator/batch_files/pm_nbi_batch_09.txt'],
                                                 'status': True,
                                                 'message': ' files are saved to pod successfully'}
        self.download_files_api_success_response = {u'total_time': u'0.01 min', u'total_seconds': 0.46767592430114746,
                                                    u'message': u'files downloaded successfully',
                                                    u'status': True,
                                                    u'files_path': [u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_00.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_01.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_02.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_03.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_04.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_05.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_06.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_07.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_08.txt',
                                                                    u'/var/tmp/fan_nbi/FAN_01_1206-08434151_u0/batch_files/pm_nbi_batch_09.txt']}

    @staticmethod
    def get_seconds_since_epoch(datetime_value):
        return (datetime_value - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()

    def tearDown(self):
        unit_test_utils.tear_down()

    # calculate_dst_offset_for_fetched_rop test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.daylight", return_value=0)
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.localtime")
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

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.daylight")
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.localtime")
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

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.daylight")
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.localtime")
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

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.daylight")
    # The offset of the local DST timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.altzone", -60 * 60)
    # The offset of the local (non-DST) timezone, in seconds west of UTC
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.timezone", 0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.localtime")
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

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
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

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.daylight", 0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.time")
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

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_log_results_of_nbi_transfer__is_successful(self, mock_logger, _):
        nbi_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_file_count"] = 11200
        fls_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_fls_file_count"] = nbi_file_count
        nbi_time = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_time"] = 300
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {}
        missed_files_count = sum(self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"].values())

        results_identifier_text = "NBI File Transfer Results for user {0}:-".format(self.user.username)

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])

        success = "True"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FLS_FILE_COUNT: {3}, TRANSFERRED_FILE_COUNT: {4}, MISSED_FILE_COUNT: {5}, "
                                "TIME_TAKEN: {6:4.2f} min, SUCCESS: {7}"
                                .format(self.collection_times["start"], self.collection_times["end"],
                                        started_at_time, fls_file_count, nbi_file_count, missed_files_count,
                                        float(nbi_time) / 60, success))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        iteration_success = True
        self.profile.log_results_of_nbi_transfer(iteration_success, self.collection_times)
        mock_logger.assert_called_with(info_to_be_logged)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_log_results_of_nbi_transfer__is_unsuccessful(self, mock_logger, _):
        nbi_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_file_count"] = 0
        fls_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_fls_file_count"] = 999
        nbi_time = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_time"] = 70
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch1": 999}
        missed_files_count = sum(self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"].values())

        results_identifier_text = "NBI File Transfer Results for user {0}:-".format(self.user.username)
        extra_text = "Note: Failures occurred - Check profile log for more details, "

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])

        success = "False"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FLS_FILE_COUNT: {3}, TRANSFERRED_FILE_COUNT: {4}, MISSED_FILE_COUNT: {5}, "
                                "TIME_TAKEN: {6:4.2f} min, {8}SUCCESS: {7}"
                                .format(self.collection_times["start"], self.collection_times["end"],
                                        started_at_time, fls_file_count, nbi_file_count,
                                        missed_files_count, float(nbi_time) / 60, success, extra_text))
        iteration_success = False
        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_transfer(iteration_success, self.collection_times)
        mock_logger.assert_called_with(info_to_be_logged)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_log_results_of_nbi_transfer__is_unsuccessful_without_missed_filecount(self, mock_logger, _):
        nbi_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_file_count"] = 0
        fls_file_count = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_fls_file_count"] = 999
        nbi_time = self.profile.nbi_transfer_stats[self.fls.user.username]["nbi_transfer_time"] = 70
        self.profile.nbi_transfer_stats[self.fls.user.username]["missed_file_count"] = {"batch1": 0}

        results_identifier_text = "NBI File Transfer Results for user {0}:-".format(self.user.username)
        extra_text = "Note: Failures occurred - Check profile log for more details, "

        started_at_time = datetime.fromtimestamp(self.collection_times["start_time_of_iteration"])

        success = "False"
        instrumentation_data = ("COLLECTED_ROP: {0} -> {1}, STARTED_AT: {2}, "
                                "FLS_FILE_COUNT: {3}, TRANSFERRED_FILE_COUNT: {4}, MISSED_FILE_COUNT: {5}, "
                                "TIME_TAKEN: {6:4.2f} min, {8}SUCCESS: {7}"
                                .format(self.collection_times["start"], self.collection_times["end"],
                                        started_at_time, fls_file_count, nbi_file_count,
                                        fls_file_count, float(nbi_time) / 60, success, extra_text))
        iteration_success = False
        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_transfer(iteration_success, self.collection_times)
        mock_logger.assert_called_with(info_to_be_logged)

    # create_pod_on_cn test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_create_pod_on_cn__is_successful(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=True, stdout="success")
        self.assertEqual(True, file_access_nbi_profiles.create_pod_on_cn("cenm168", "path", "fan-01"))
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_create_pod_on_cn__raises_environ_error(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, file_access_nbi_profiles.create_pod_on_cn, "cenm168", "path", "fan-01")
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    # delete_pod_on_cn test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_delete_pod_on_cn__is_successful(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=True, stdout="success")
        self.assertEqual(True, file_access_nbi_profiles.delete_pod_on_cn("cenm168", "fan-01"))
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_delete_pod_on_cn__raises_environ_error(self, mock_local_cmd, mock_cmd, mock_debug_log):
        mock_local_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, file_access_nbi_profiles.delete_pod_on_cn, "cenm168", "fan-01")
        self.assertEqual(mock_local_cmd.call_count, 1)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    # check_fileaccessnbi_is_running test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.run_local_cmd")
    def test_check_fileaccessnbi_is_running__is_successful(self, mock_local_cmd, mock_cmd):
        mock_local_cmd.return_value = Mock(ok=True)
        self.profile.NAME = 'FAN_12'
        self.assertEqual(True, file_access_nbi_profiles.check_fileaccessnbi_is_running("cenm618"))
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.run_local_cmd")
    def test_check_fileaccessnbi_is_running__if_not_running(self, mock_local_cmd, mock_cmd):
        mock_local_cmd.return_value = Mock(ok=False)
        self.assertRaises(EnvironError, file_access_nbi_profiles.check_fileaccessnbi_is_running, "cenm618")
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 1)

    # execute_flow test cases

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_and_add_new_datatypes_to_datatype_fileid_dict")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_fan_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, True, False])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_fileaccessnbi_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__is_successful(self, mock_create_users, mock_perform_fan_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_fan_operations.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_fan_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_and_add_new_datatypes_to_datatype_fileid_dict")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_fileaccessnbi_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__is_successful_for_fan_12(self, mock_create_users, mock_perform_fan_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.NAME = 'FAN_12'
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_fan_operations.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_fan_nbi_directory")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_fileaccessnbi_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__is_successful_for_fan_12_again(self, mock_create_users, mock_perform_fan_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.count = 1
        self.profile.NAME = 'FAN_12'
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_fan_operations.call_count, 0)

    # set_pib_parameters test cases
    @patch('enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_pib_value_on_enm',
           return_value='False')
    @patch('enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.update_pib_parameter_on_enm')
    def test_set_pib_parameters(self, mock_logger_debug, mock_get_pib_value, mock_update_pib_parameter):
        mock_get_pib_value.side_effect = ['false', 'False', True, 'True', False, 'true']

        file_access_nbi_profiles.set_pib_parameters("true")
        self.assertEqual(mock_logger_debug.call_count, 2)
        self.assertEqual(mock_get_pib_value.call_count, 3)
        self.assertEqual(mock_update_pib_parameter.call_count, 4)

    @patch('enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.set_pib_parameters')
    def test_enabled_parameters_successful(self, mock_set_pib_parameters):
        profile = Mock()

        profile.DESIRED_TIME = datetime.now().strftime("%H:%M")

        file_access_nbi_profiles.check_pib_parameters_enabled(profile)

        mock_set_pib_parameters.assert_called_with("true")

    def test_enabled_parameters_unsuccessful(self):
        profile = Mock()

        profile.DESIRED_TIME = "14:20"

        file_access_nbi_profiles.check_pib_parameters_enabled(profile)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_fileaccessnbi_is_running",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__if_fileaccessnbi_service_not_running(self, mock_create_users, mock_perform_fan_operations,
                                                                *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_fan_operations.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_fileaccessnbi_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=False)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__if_create_pod_on_cn_is_failed(self, mock_create_users, mock_perform_fan_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_fan_operations.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_fileaccessnbi_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__if_fan01_is_not_running(self, mock_create_users, mock_perform_fan_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertEqual(mock_create_users.call_count, 1)
        self.assertEqual(mock_perform_fan_operations.call_count, 1)

    # perform_file_access_nbi_operations test cases

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "set_collection_times")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "log_results_of_nbi_transfer")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.requests.post")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_perform_file_access_nbi_operations__is_successful(self, mock_debug_log, mock_requests_post, *_):
        post_response = Mock(status_code=200)
        post_response.json.return_value = self.fetch_files_api_success_response
        mock_requests_post.return_value = post_response
        self.profile.perform_file_access_nbi_operations("fan-01")
        self.assertEqual(mock_debug_log.call_count, 11)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "set_collection_times")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "log_results_of_nbi_transfer")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.requests.post")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_perform_file_access_nbi_operations__is_unsuccessful(self, mock_debug_log, mock_requests_post, mock_add_error, *_):
        post_response = Mock(status_code=200)
        fetch_files_api_success_response = {'total_time': '0.87 min', 'total_seconds': 52.400402307510376,
                                            'message': 'Exception does not take keyword arguments', 'file_locations': [],
                                            'files': 0, 'data_types_dict': {}, 'status': False}

        post_response.json.return_value = fetch_files_api_success_response
        mock_requests_post.return_value = post_response
        self.profile.perform_file_access_nbi_operations("fan-01")
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertTrue(call(EnvironError in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.requests.post",
           return_value=Mock(status_code=201))
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "set_collection_times")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "log_results_of_nbi_transfer")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_perform_file_access_nbi_operations__add_error_as_exception(self, mock_debug_log, mock_add_error, *_):
        self.profile.perform_file_access_nbi_operations("fan-01")
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertTrue(call(EnvironError in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.cache.is_enm_on_cloud_native",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "create_fan_pod_yaml_config_file_for_fan")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_enm_cloud_native_namespace",
           return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.get_apache_url",
           return_value="enmurl")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "keep_running", side_effect=[True, False, True])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.partial")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.delete_pod_on_cn")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.create_pod_on_cn", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.check_pod_is_running",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "perform_file_access_nbi_operations")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.create_users")
    def test_execute_flow__add_error_as_exception(self, mock_create_users, mock_debug_log,
                                                  mock_add_error, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 5)
        self.assertTrue(call(EnvironError in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.run_local_cmd")
    def test_check_pod_is_running__is_successful(self, mock_local_cmd, mock_cmd, mock_debug_log, mock_timedelta,
                                                 mock_datetime, *_):
        mock_local_cmd.side_effect = [Mock(stdout="Pending"), Mock(stdout="Pending"), Mock(stdout="Running")]
        time_now = datetime(2022, 9, 6, 9, 0, 0)
        expiry_time = datetime(2022, 9, 6, 9, 9, 2, 0)
        mock_datetime.now.return_value = time_now
        mock_timedelta.return_value = expiry_time - time_now
        file_access_nbi_profiles.check_pod_is_running("path", "fan-01")
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_cmd.call_count, 3)
        self.assertEqual(mock_local_cmd.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.datetime")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.timedelta")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.run_local_cmd")
    def test_check_pod_is_running__raises_timeout_error(self, mock_local_cmd, mock_cmd, mock_debug_log,
                                                        mock_timedelta, mock_datetime, *_):
        mock_local_cmd.side_effect = [Mock(stdout="Pending"), Mock(stdout="Pending"), Mock(stdout="Running")]
        time_now = datetime(2022, 9, 6, 9, 0, 0)
        expiry_time = datetime(2022, 9, 6, 9, 9, 2, 0)
        mock_datetime.now.side_effect = [time_now, time_now, expiry_time]
        mock_timedelta.return_value = expiry_time - time_now
        self.assertRaises(TimeOutError, file_access_nbi_profiles.check_pod_is_running, "enmcc1", "fan-01")
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_cmd.call_count, 1)
        self.assertEqual(mock_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.os.path.join", return_value="test.yaml")
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_create_fan_pod_yaml_config_file_for_fan__is_successful(self, mock_debug_log, mock_filesystem, mock_read,
                                                                    _):
        mock_read.return_value.readlines.return_value = ["line1\n", "podname\n", "line2\n", "podcpu", "podmemory", "enmurl"]
        mock_filesystem.does_dir_exist.return_value = True
        self.profile.enm_url = 'https://ieatenm5432-1.athtem.eei.ericsson.se'
        self.profile.create_fan_pod_yaml_config_file_for_fan()
        self.assertEqual(mock_debug_log.call_count, 6)
        self.assertEqual(mock_read.return_value.readlines.call_count, 1)
        self.assertEqual(mock_filesystem.does_dir_exist.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.os.path.join", return_value="test.yaml")
    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_create_fan_pod_yaml_config_file_for_fan__if_fan_dir_already_existed(self, mock_debug_log,
                                                                                 mock_filesystem, mock_read, _):
        mock_read.return_value.readlines.return_value = ["line1\n", "podname\n", "line2\n"]
        mock_filesystem.does_dir_exist.return_value = False

        self.profile.create_fan_pod_yaml_config_file_for_fan()
        self.assertEqual(mock_debug_log.call_count, 6)
        self.assertEqual(mock_read.return_value.readlines.call_count, 1)
        self.assertEqual(mock_filesystem.does_dir_exist.call_count, 1)

    #  check_fan_nbi_directory test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem.does_dir_exist")
    def test_check_fan_nbi_directory__doesnt_exist(self, mock_does_dir_exist, mock_run_local_cmd, mock_debug_log,
                                                   *_):
        mock_does_dir_exist.return_value = False
        self.profile.check_fan_nbi_directory(self.user.username)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem.does_dir_exist")
    def test_check_fan_nbi_directory__if_dir_exist(self, mock_does_dir_exist, mock_run_local_cmd, mock_debug_log,
                                                   *_):
        mock_does_dir_exist.return_value = True
        self.profile.check_fan_nbi_directory(self.user.username)
        self.assertEqual(0, mock_run_local_cmd.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    #  clear_fan_nbi_dir test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_clear_fan_nbi_dir__is_successful(self, mock_run_local_cmd, _):
        file_access_nbi_profiles.clear_fan_nbi_dir(self.profile)
        self.assertEqual(1, mock_run_local_cmd.call_count)

    # clear_fan_pid_file test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.filesystem.does_file_exist",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_clear_fan_pid_file__is_successful(self, mock_run_local_cmd, *_):
        self.profile.clear_fan_pid_file(self.user.username)
        self.assertEqual(1, mock_run_local_cmd.call_count)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.execute_flow")
    def test_run__in_fan_11_is_successful(self, mock_execute_flow):
        FAN_11().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.execute_flow")
    def test_run__in_fan_12_is_successful(self, mock_execute_flow):
        FAN_12().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.execute_flow")
    def test_run__in_fan_13_is_successful(self, mock_execute_flow):
        FAN_13().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile.execute_flow")
    def test_run__in_fan_14_is_successful(self, mock_execute_flow):
        FAN_14().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    # safe_teardown test cases
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.shell.run_local_cmd")
    def test_safe_teardown__is_successful(self, mock_run_local_cmd, _):
        file_access_nbi_profiles.safe_teardown(self.profile.KILL_RUNNING_KUBECTL_COMMANDS_PROCESSES.format(
            username=self.user.username), self.profile.FAN_PIDS_FILE.format(username=self.user.username))
        self.assertEqual(2, mock_run_local_cmd.call_count)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.requests.post")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_download_multiple_batch_files_to_pod_with_api__is_successful(self, mock_debug_log, mock_requests_post, *_):
        post_response = Mock(status_code=200)
        post_response.json.return_value = self.download_files_api_success_response
        mock_requests_post.return_value = post_response
        curl_end_time = 600
        file_access_nbi_profiles.download_multiple_batch_files_to_pod_with_api(['batch1', 'batch2'],
                                                                               "testpod", curl_end_time, self.profile)
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.FileAccessNbiProfile."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.requests.post")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    def test_download_multiple_batch_files_to_pod_with_api__add_error_exception(self, mock_debug_log,
                                                                                mock_requests_post, mock_add_error,
                                                                                *_):
        mock_requests_post.return_value = Mock(status_code=201)
        curl_end_time = 600
        file_access_nbi_profiles.download_multiple_batch_files_to_pod_with_api(['batch1', 'batch2'],
                                                                               "testpod", curl_end_time,
                                                                               self.profile)
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertTrue(call(EnvironError in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*',
                                                                                      'PM_UETRACE'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.datetime")
    def test_check_and_add_new_datatypes_to_datatype_fileid_dict__is_successful(self, mock_datetime, mock_debug_log, _):
        mock_datetime.now.return_value = datetime(2024, 02, 12, 0, 0, 0)
        self.profile.check_and_add_new_datatypes_to_datatype_fileid_dict()
        self.assertEqual(mock_debug_log.call_count, 6)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.datetime")
    def test_check_and_add_new_datatypes_to_datatype_fileid_dict__if_no_datatype_found(self, mock_datetime,
                                                                                       mock_debug_log, _):
        mock_datetime.now.return_value = datetime(2024, 02, 12, 0, 0, 0)
        self.profile.check_and_add_new_datatypes_to_datatype_fileid_dict()
        self.assertEqual(mock_debug_log.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles."
           "get_matched_supported_datatypes_with_configured_datatypes", return_value=['PM_STATISTICAL',
                                                                                      'PM_UETR', 'TOPOLOGY_*'])
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles.datetime.datetime")
    def test_check_and_add_new_datatypes_to_datatype_fileid_dict__if_time_is_different(self, mock_datetime,
                                                                                       mock_debug_log, _):
        mock_datetime.now.return_value = datetime(2024, 02, 12, 4, 0, 0)
        self.profile.check_and_add_new_datatypes_to_datatype_fileid_dict()
        self.assertEqual(mock_debug_log.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
