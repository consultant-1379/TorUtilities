#!/usr/bin/env python

from datetime import datetime

import unittest2
from mock import patch, Mock
from pytz import timezone, utc
from enmutils_int.lib.pm_nbi import Fls
from enmutils_int.lib.profile_flows.fan_flows import file_access_nbi_profile
from enmutils_int.lib.workload.fan_01 import FAN_01
from enmutils_int.lib.workload.fan_02 import FAN_02
from enmutils_int.lib.workload.fan_03 import FAN_03
from enmutils_int.lib.workload.fan_04 import FAN_04
from testslib import unit_test_utils


class FAN01ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")
        self.fls = Fls(user=self.user)
        self.profile = file_access_nbi_profile.FileAccessNbiProfile()
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

        self.profile.nbi_transfer_stats[self.user.username] = {"nbi_transfer_time": 0, "nbi_fls_file_count": 0,
                                                               "missed_file_count": {}}
        self.profile.data_type_file_id_dict = {self.user.username: {'PM_CELLTRACE': [0, None],
                                                                    'PM_STATISTICAL': [2, None],
                                                                    'PM_CTUM': [0, None]}}
        self.profile.users = [self.user]
        self.profile.fan01_pod_ip = ["ip"]
        self.profile.enm_url = None
        self.profile.FAN_NBI_BATCH_FILENAME = "/tmp/test"
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

    # get_files_to_collect tests
    def test_get_files_to_collect__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.get_files_to_collect("profile", "fls")

    # get_list_of_files_from_fls test cases
    def test_get_list_of_files_from_fls__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.get_list_of_files_from_fls("fls")

    # calculate_dst_offset_for_fetched_rop test cases

    def test_calculate_dst_offset_for_fetched_rop__returns_minus_60_if_dst_inactive_for_current_time_but_active_for_rop(
            self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.calculate_dst_offset_for_fetched_rop(9999)

    # set_collection_times tests
    def test_set_collection_times__returned_dict_contains_correct_elements(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.set_collection_times()

    def test_log_into_enm_from_pod__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.log_into_enm_from_pod("fan_pod_ip")

    # log_results_of_nbi_transfer tests

    def test_log_results_of_nbi_transfer__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.log_results_of_nbi_transfer(Mock())

    # create_pod_on_cn test cases

    def test_create_pod_on_cn__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.create_pod_on_cn("cenm168", "path", "fan-01")

    # delete_pod_on_cn test cases
    def test_delete_pod_on_cn__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.delete_pod_on_cn("cenm168", "fan-01")

    # download_files_to_pod test cases

    def test_download_files_to_pod___is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.download_files_to_pod(Mock(), "fan-01", self.profile)

    # check_fileaccessnbi_is_running test cases

    def test_check_fileaccessnbi_is_running__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.check_fileaccessnbi_is_running("cenm618")

    # execute_flow test cases
    def test_execute_flow__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.execute_flow()

    # perform_file_access_nbi_operations test cases
    def test_perform_file_access_nbi_operations__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.perform_file_access_nbi_operations("fan-01")

    def test_check_pod_is_running__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.check_pod_is_running("path", "fan-01")

    def test_create_fan_pod_yaml_config_file_for_fan__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.create_fan_pod_yaml_config_file_for_fan()

    #  transfer_batch_files_to_pod test cases
    def test_transfer_batch_files_to_pod__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.transfer_batch_files_to_pod()

    #  check_fan_nbi_directory test cases
    def test_check_fan_nbi_directory__doesnt_exist(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.check_fan_nbi_directory(self.user.username)

    #  clear_fan_nbi_dir test cases
    def test_clear_fan_nbi_dir__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.clear_fan_nbi_dir(self.profile)

    # clear_fan_pid_file test cases
    def test_clear_fan_pid_file__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.clear_fan_pid_file(self.user.username)

    #  create_batch_files_on_server test cases
    def test_create_batch_files_on_server__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        self.profile.create_batch_files_on_server(["file1", "file2", "file3"])

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.PlaceHolderFlow")
    def test_run__in_fan_01_is_successful(self, _):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        FAN_01().run()

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.PlaceHolderFlow")
    def test_run__in_fan_02_is_successful(self, _):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        FAN_02().run()

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.PlaceHolderFlow")
    def test_run__in_fan_03_is_successful(self, _):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        FAN_03().run()

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.PlaceHolderFlow")
    def test_run__in_fan_04_is_successful(self, _):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        FAN_04().run()

    # monitor_sftp_file_transfer tests

    def test_monitor_fan_files_download__all_processes_gone_after_iteration_ends(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.monitor_fan_files_download(self.collection_times, self.user.username, self.profile)

    # check_that_fan_curl_processes_are_complete test cases
    def test_check_that_fan_curl_processes_are_complete__is_successful(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.check_that_fan_curl_processes_are_complete(self.profile, self.user.username, 1000,
                                                                           10, 5, 120)

    #  any_fan_curl_processes_still_running test cases
    def test_any_fan_curl_processes_still_running__returns_true_if_processes_still_running(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.any_fan_curl_processes_still_running("1", self.profile, self.user.username, 1234)

    # safe_teardown test cases
    def test_safe_teardown__is_successful(self,):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.safe_teardown(Mock(), Mock())

    # tq_task_executor tests

    def test_tq_task_executor_call_fan_task(self):
        """
        Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
        """
        file_access_nbi_profile.tq_task_executor(Mock(), self.profile)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
