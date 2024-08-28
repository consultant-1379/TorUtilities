#!/usr/bin/env python
import json
import datetime
import time
from testslib import unit_test_utils
import unittest2
from mock import patch, Mock, PropertyMock, call
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.lt_syslog_stream_flows import lt_syslog_stream_flow
from enmutils_int.lib.workload.lt_syslog_stream_01 import LT_SYSLOG_STREAM_01
from pytz import timezone
from dateutil.tz import tzutc


class LtSysLogStreamFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")
        self.profile = lt_syslog_stream_flow.LtSysLogStreamFlow()
        self.profile.users = [self.user]
        self.profile.USER_ROLES = ['ADMINISTRATOR']
        self.profile.NUM_USERS = 1
        self.profile.SCHEDULED_TIMES_STRINGS = ["{0}:{1}:00".format(hour, minute) for hour in range(00, 24)
                                                for minute in range(0, 60, 28) if minute in [28, 56]]
        self.tz = timezone("Europe/Dublin")
        self.profile.NUM_OF_LOGS = 1
        self.response = ('{"priority":"174", "timestamp":"2023-08-08T05:40:00.034+00:00", '
                         '"timegenerated":"2023-08-08T04:40:00.152667+00:00", "facility_code":"21",'
                         '"facility":"local5", "severity_code":"6", "severity":"info", '
                         '"hostname":"pmrouterpolicy-dc8bf8974-kt962", "program":"JBOSS",'
                         '"tag":"JBOSS[1]", "message":"5856ccfc8-wkmjqmediationservice7.11.115"}')

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow."
           "get_enm_cloud_native_namespace", return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_if_syslog_namespace_exists")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow."
           "get_pod_info_in_cenm", return_value=["pod"])
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "lt_sys_log_stream_operations")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "create_users")
    def test_execute_flow__is_successful(self, mock_create_users, mock_lt_sys_log_stream_operations, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_lt_sys_log_stream_operations.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow."
           "get_enm_cloud_native_namespace", return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_if_syslog_namespace_exists")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "sleep_until_time", return_value=0)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow."
           "get_pod_info_in_cenm", side_effect=[EnvironError("pod not found")])
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "lt_sys_log_stream_operations")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "create_users")
    def test_execute_flow__if_pod_is_not_found(self, mock_create_users, mock_lt_sys_log_stream_operations,
                                               mock_add_error, *_):
        mock_create_users.return_value = [Mock(username="test")]
        self.profile.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_lt_sys_log_stream_operations.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    #  verify_metrics_received_into_pod test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.time.time")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "get_logs_from_syslog_pod")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "parse_results")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "log_results_of_nbi_metrics_received")
    def test_verify_metrics_received_into_pod__is_success(self, mock_log_results, mock_get_pod_logs,
                                                          mock_parse_results, _):
        self.profile.verify_metrics_received_into_pod()
        self.assertTrue(mock_log_results.called)
        self.assertTrue(mock_get_pod_logs.called)
        self.assertTrue(mock_parse_results.called)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "verify_metrics_received_into_pod")
    def test_lt_sys_log_stream_operations__is_success(self, mock_verify_metrics_received_into_pod, _):
        self.profile.lt_sys_log_stream_operations()
        self.assertTrue(mock_verify_metrics_received_into_pod.called)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "verify_metrics_received_into_pod")
    def test_lt_sys_log_stream_operations__add_error(self, mock_verify_metrics_received_into_pod, mock_add_error):
        mock_verify_metrics_received_into_pod.side_effect = EnvironError("error")
        self.profile.lt_sys_log_stream_operations()
        self.assertTrue(mock_verify_metrics_received_into_pod.called)
        self.assertTrue(mock_add_error.called)

    # log_results_of_nbi_transfer tests
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_log_results_of_nbi_metrics_received__is_successful(self, mock_logger, _):
        self.profile.nbi_transfer_stats = {"failed_timestamps": []}
        failed_timestamps = "FAILED_TIMESTAMPS: {0}".format(self.profile.nbi_transfer_stats["failed_timestamps"])
        verified_logs_count = "VERIFIED_LOGS_COUNT: {0}".format(self.profile.NUM_OF_LOGS)
        failed_logs_count = "FAILED_LOGS_COUNT: {0}".format(len(self.profile.nbi_transfer_stats["failed_timestamps"]))

        metric_count_text = "{0}, {1}, {2}".format(verified_logs_count, failed_logs_count, failed_timestamps)
        results_identifier_text = "SYS Logs metrics received Results for user {0}:-".format(self.user.username)
        timestamp = int(time.time())
        started_at_time = datetime.datetime.fromtimestamp(int(time.time()))

        instrumentation_data = ("PROFILE_START_TIME: {0}, {1}, RESULT: {2}"
                                .format(started_at_time, metric_count_text, "PASS"))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_metrics_received(timestamp)
        mock_logger.assert_called_with(info_to_be_logged)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.syslog.syslog")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_log_results_of_nbi_metrics_received__is_unsuccessful(self, mock_logger, _):
        self.profile.nbi_transfer_stats = {"failed_timestamps": [{'timestamp': u'2023-08-07T12:28:00.413+00:00',
                                                                  'hostname': u'netex-c979478c5-kr42h',
                                                                  'timegenerated': u'2023-08-07T11:28:00.516704+00:00'},
                                                                 {'timestamp': u'2023-08-07T12:28:00.572+00:00',
                                                                  'hostname': u'netex-c979478c5-kr42h',
                                                                  'timegenerated': u'2023-08-07T11:28:00.690463+00:00'}]}
        failed_timestamps = "FAILED_TIMESTAMPS: {0}".format(self.profile.nbi_transfer_stats["failed_timestamps"])
        verified_logs_count = "VERIFIED_LOGS_COUNT: {0}".format(self.profile.NUM_OF_LOGS)
        failed_logs_count = "FAILED_LOGS_COUNT: {0}".format(len(self.profile.nbi_transfer_stats["failed_timestamps"]))
        metric_count_text = "{0}, {1}, {2}".format(verified_logs_count, failed_logs_count, failed_timestamps)
        results_identifier_text = "SYS Logs metrics received Results for user {0}:-".format(self.user.username)
        extra_text = "Note: Few logs are not received (streamed) to syslog receiver with in 1 minute, "
        timestamp = int(time.time())
        started_at_time = datetime.datetime.fromtimestamp(int(time.time()))

        instrumentation_data = ("PROFILE_START_TIME: {0}, "
                                "{1}, {2}RESULT: {3}"
                                .format(started_at_time,
                                        metric_count_text, extra_text, "FAIL"))

        info_to_be_logged = "{0} {1} {2}".format(self.profile.NAME, results_identifier_text, instrumentation_data)
        self.profile.log_results_of_nbi_metrics_received(timestamp)
        mock_logger.assert_called_with(info_to_be_logged)

    #  get_pod_timezone test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.Command")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.re.search")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_get_pod_timezone__is_success(self, mock_log, mock_run_cmd, mock_search, *_):
        mock_run_cmd.return_value = Mock(ok=True, stdout="Z:                         Europe/Dublin\n"
                                                         "TZ:                         Europe/Dublin ")
        mock_search_result = Mock()
        mock_search_result.group.return_value = "Europe/Dublin"
        mock_search.return_value = mock_search_result
        self.profile.get_pod_timezone()
        self.assertTrue(mock_run_cmd.called)
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.Command")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.re.search")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_get_pod_timezone__is_unsuccessful(self, mock_log, mock_run_cmd, *_):
        mock_run_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, self.profile.get_pod_timezone)
        self.assertTrue(mock_run_cmd.called)
        self.assertEqual(mock_log.call_count, 2)

    #  get_logs_from_syslog_pod test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_get_logs_from_syslog_pod__is_success(self, mock_log, mock_run_cmd, _):
        mock_run_cmd.return_value = Mock(ok=True, stdout=self.response)
        self.profile.get_logs_from_syslog_pod()
        self.assertTrue(mock_run_cmd.called)
        self.assertEqual(mock_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_get_logs_from_syslog_pod__is_unsuccessful(self, mock_log, mock_run_cmd, *_):
        mock_run_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, self.profile.get_logs_from_syslog_pod)
        self.assertTrue(mock_run_cmd.called)
        self.assertEqual(mock_log.call_count, 2)

    #  check_if_syslog_namespace_exists test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_check_if_syslog_namespace_exists__is_successful(self, mock_log, mock_run_cmd):
        mock_run_cmd.return_value = Mock(ok=True, stdout="syslog              Active   6d18h")
        self.profile.check_if_syslog_namespace_exists()
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_run_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    def test_check_if_syslog_namespace_exists___is_unsuccessful(self, mock_log, mock_run_cmd):
        mock_run_cmd.return_value = Mock(ok=False, stdout="error")
        self.assertRaises(EnvironError, self.profile.check_if_syslog_namespace_exists)
        self.assertEqual(mock_log.call_count, 0)
        self.assertEqual(mock_run_cmd.call_count, 1)

    #  parse_results test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "verify_if_log_is_failed", return_value=True)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "get_pod_timezone", return_value="Europe/Dublin")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.parse")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.json")
    def test_parse_results__is_unsuccessful(self, mock_json, mock_parse, mock_debug, mock_add_error, *_):
        mock_json.loads.return_value = json.loads(self.response)
        mock_parse.side_effect = [datetime.datetime(2023, 8, 8, 5, 40, 0,
                                                    34000, tzinfo=tzutc()),
                                  datetime.datetime(2023, 8, 8, 4, 41, 1,
                                                    152667, tzinfo=tzutc())]
        self.profile.parse_results(self.response)
        self.assertEqual(mock_debug.call_count, 1)
        message = ("[{'hostname': u'pmrouterpolicy-dc8bf8974-kt962', "
                   "'timegenerated': u'2023-08-08T04:40:00.152667+00:00'}]....., 1 logs are not received to syslog "
                   "receiver with in 1 minute. Please check logs")
        self.assertTrue(call(EnvironError(message) in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "verify_if_log_is_failed", return_value=False)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "get_pod_timezone", return_value="Europe/Dublin")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.parse")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.json")
    def test_parse_results__is_successful(self, mock_json, mock_parse, mock_debug, *_):
        mock_json.loads.return_value = json.loads(self.response)
        mock_parse.side_effect = [datetime.datetime(2023, 8, 8, 5, 40, 0,
                                                    34000, tzinfo=tzutc()),
                                  datetime.datetime(2023, 8, 8, 4, 40, 2,
                                                    34010, tzinfo=tzutc())]

        self.profile.parse_results(self.response)
        self.assertEqual(mock_debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "verify_if_log_is_failed", return_value=True)
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "get_pod_timezone", return_value="Europe/Dublin")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.parse")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.json")
    def test_parse_results__if_one_hour_two_minutes(self, mock_json, mock_parse, mock_debug, mock_add_error, *_):
        mock_json.loads.return_value = json.loads(self.response)
        mock_parse.side_effect = [datetime.datetime(2023, 8, 8, 5, 40, 0,
                                                    34000, tzinfo=tzutc()),
                                  datetime.datetime(2023, 8, 8, 4, 42, 1,
                                                    152667, tzinfo=tzutc())]
        self.profile.parse_results(self.response)
        self.assertEqual(mock_debug.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)

    # get_pod_info_in_cenm test cases
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.Command")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow"
           ".run_local_cmd")
    def test_get_pod_info_in_cenm__is_successful(self, mock_run_local_cmd, mock_command, mock_debug):
        output = "eric-enm-syslog-receiver-786                       1/1     Running     0          10h\n"
        mock_run_local_cmd.return_value = Mock(ok=True, stdout=output)
        self.assertEqual("eric-enm-syslog-receiver-786",
                         lt_syslog_stream_flow.get_pod_info_in_cenm("eric-enm-syslog-receiver", "syslog"))
        self.assertEqual(mock_debug.call_count, 2)
        self.assertEqual(mock_command.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.Command")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow"
           ".run_local_cmd")
    def test_get_pod_info_in_cenm__raises_environerror_if_kubectl_cmd_execution_has_problems(
            self, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value = Mock(ok=False, stdout="")
        self.assertRaises(EnvironError, lt_syslog_stream_flow.get_pod_info_in_cenm, "cmserv", "syslog")

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.Command")
    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow"
           ".run_local_cmd")
    def test_get_pod_info_in_cenm__if_pod_not_running(self, mock_run_local_cmd, mock_command, mock_debug):
        output = "eric-enm-syslog-receiver-786                       1/1     ContainerCreating     0          10h\n"
        mock_run_local_cmd.return_value = Mock(ok=True, stdout=output)
        self.assertRaises(EnvironError, lt_syslog_stream_flow.get_pod_info_in_cenm, "cmserv", "syslog")
        self.assertEqual(mock_debug.call_count, 1)
        self.assertEqual(mock_command.call_count, 1)

    # verify_if_log_is_failed tes cases
    def test_verify_if_log_is_failed__is_successful(self):
        self.assertEqual(False, self.profile.verify_if_log_is_failed(59, 0))

    def test_verify_if_log_is_failed__if_hour_one_minute(self):
        self.assertEqual(False, self.profile.verify_if_log_is_failed(3660, 1))

    def test_verify_if_log_is_failed__if_hour_two_minute(self):
        self.assertEqual(True, self.profile.verify_if_log_is_failed(3720, 2))

    def test_verify_if_log_is_failed__if_hour_two_minute_one_second(self):
        self.assertEqual(True, self.profile.verify_if_log_is_failed(3720, 2.1))

    def test_verify_if_log_is_failed__if_45_minutes(self):
        self.assertEqual(True, self.profile.verify_if_log_is_failed(2700, 0))

    @patch("enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow.LtSysLogStreamFlow."
           "execute_flow")
    def test_run_in_lt_syslog_stream_01__is_successful(self, mock_execute_flow):
        LT_SYSLOG_STREAM_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    def tearDown(self):
        unit_test_utils.tear_down()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
