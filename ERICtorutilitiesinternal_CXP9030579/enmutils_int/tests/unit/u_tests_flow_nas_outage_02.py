# !/usr/bin/env python
import unittest2
from mock import patch, PropertyMock, Mock
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.workload.nas_outage_02 import NAS_OUTAGE_02
from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02 import NasOutage02Flow, get_service_status, \
    check_status_of_nas, execute_nas_command, retry_status_check


class NasOutage02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = NasOutage02Flow()
        self.flow.SLEEP_TIME = 5

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def test_get_service_status__online():
        get_service_status("grep host", host="host")

    @staticmethod
    def test_get_service_status__offline():
        get_service_status("B  Managementonsole host       Y          N               OFFLINE", host="host")

    @staticmethod
    def test_get_service_status__nas_slave_faulted():
        get_service_status("B  ManagementConsole host       Y          N               OFFLINE|FAULTED", host="host")

    @staticmethod
    def test_get_service_status__nas_head_faulted():
        get_service_status("B  ManagementConsole       Y          N               OFFLINE|FAULTED", host="host")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow."
           "sleep_until_next_scheduled_iteration")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.state",
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas", return_value="ONLINE")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.is_nas_accessible", return_value=True)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_health_check",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.get_nas_instances",
           return_value=["ab", "bc", "DE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_instance_change")
    def test_execute_flow__success(self, mock_nas, mock_get_nas, mock_debug_log, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_debug_log.call_count, 7)
        self.assertEqual(mock_get_nas.call_count, 1)
        self.assertEqual(mock_nas.call_count, 4)
        self.assertEqual(mock_add_error.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_for_active_litp_plan",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.Command')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.run_cmd_on_ms")
    def test_nas_health_check__success(self, mock_cmd, *_):
        response = Mock()
        response.stdout = "Str\nstr\nstr\nstr\nNAS HEALTHCHECK: PASSED"
        response.rc = 0
        mock_cmd.return_value = response
        self.flow.nas_health_check()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_for_active_litp_plan",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.Command')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.run_cmd_on_ms")
    def test_nas_health_check__failure(self, mock_cmd, *_):
        response = Mock()
        response.stdout = ""
        response.rc = 0
        mock_cmd.return_value = response
        self.flow.nas_health_check()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_for_active_litp_plan",
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.Command')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.run_cmd_on_ms")
    def test_nas_health_check__Environ_Error(self, mock_cmd, *_):
        response = Mock()
        response.stdout = ""
        response.rc = 1
        mock_cmd.return_value = response
        self.assertRaises(EnvironError, self.flow.nas_health_check)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_for_active_litp_plan",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.Command')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.run_cmd_on_ms")
    def test_nas_health_check_failure(self, *_):
        self.flow.nas_health_check()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow."
           "sleep_until_next_scheduled_iteration")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas")
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.is_nas_accessible", return_value=False)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.get_nas_instances",
           return_value=["ab", "bc", "de"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_instance_change")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.add_error_as_exception")
    def test_execute_flow__Error(self, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow."
           "sleep_until_next_scheduled_iteration")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas", return_value="OFFLINE")
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.get_nas_instances",
           return_value=["ab", "bc", "de"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_instance_change")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.is_nas_accessible")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_health_check",
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.add_error_as_exception")
    def test_execute_flow__status_check_failed(self, mock_add_error, mock_nas, *_):
        mock_nas.return_value = True
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow."
           "sleep_until_next_scheduled_iteration")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas", return_value="ONLINE")
    @patch('enmutils_int.lib.profile.Profile.keep_running', side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.partial")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.get_nas_instances",
           return_value=["ab", "bc", "de"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_instance_change")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.is_nas_accessible")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.nas_health_check",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.add_error_as_exception")
    def test_execute_flow__health_check_failed(self, mock_add_error, mock_health, mock_nas, *_):
        mock_nas.return_value = True
        mock_health.side_effect = [True, False]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.execute_flow")
    def test_run__nas_outage_02_is_successful(self, _):
        nas_outage_02 = NAS_OUTAGE_02()
        nas_outage_02.run()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__is_successful_with_start(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 0, 0]
        self.flow.nas_instance_change("start", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__success_stop(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 0, 0]
        self.flow.nas_instance_change("stop", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__if_lms_login_failed(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [1, 1, 0, 0, 0, 0]
        self.assertRaises(EnvironError, self.flow.nas_instance_change, "start", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__if_nas_login_failed(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 1, 0]
        self.assertRaises(EnvironError, self.flow.nas_instance_change, "start", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__if_nas_head_login_failed(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 1, 1, 0]
        self.assertRaises(EnvironError, self.flow.nas_instance_change, "stop", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__if_nas_login_pwd_propmpt_not_appear(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0]
        self.assertRaises(EnvironError, self.flow.nas_instance_change, "start", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__if_nas_login_pwd_does_not_propmpt(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 2, 0, 0, 0, 0]
        self.assertRaises(EnvironError, self.flow.nas_instance_change, "configure", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.execute_nas_command")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_nas_instance_change__if_nas_login_pwd_not_given(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 1, 1, 0, 0, 0]
        self.assertRaises(EnvironError, self.flow.nas_instance_change, "configure", "cmd", "host", "password")
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__success(self, mock_spawn, mock_find, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0]
        mock_find.side_effect = [["hieatnas180181_01", "ieatnas180181_01"], ["ieatnas180181_01", "ieatnas180181_02"]]
        self.flow.get_nas_instances()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__success_1(self, mock_spawn, mock_find, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0]
        mock_find.side_effect = [["hieatnas180181_01", "hieatnas180181_01"], ["ieatnas180181_01", "ieatnas180181_02"]]
        self.flow.get_nas_instances()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__if_lms_login_failed(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [1, 0, 0, 0, 0]
        self.flow.get_nas_instances()
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__if_nas_login_failed(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 0, 0]
        self.flow.get_nas_instances()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall', side_effect=[['l', 'i']])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__cmd_execution_failed(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 1, 0]
        self.flow.get_nas_instances()
        self.assertEqual(mock_debug_log.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__if_nas_login_pwd_does_not_propmpt(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 1, 0, 0]
        self.flow.get_nas_instances()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall')
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__child(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 1, 1, 1]
        self.flow.get_nas_instances()
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.NasOutage02Flow.fetch_password_from_litp")
    @patch('enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.re.findall', side_effect=[['l', 'i'],
                                                                                                    ['k', 'o']])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug",
           side_effect=['q', 'w', 'e', 'r', 't', 'y', Exception])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_get_nas_instances__Exception(self, mock_spawn, mock_debug_log, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 1]
        self.assertRaises(Exception, self.flow.get_nas_instances)
        self.assertEqual(mock_debug_log.call_count, 9)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.run_cmd_on_ms")
    def test_fetch_password_from_litp__success(self, mock_run_local_cmd, *_):
        response = Mock()
        response.stdout = "something"
        mock_run_local_cmd.return_value = response
        self.flow.fetch_password_from_litp()

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.run_cmd_on_ms")
    def test_fetch_password_from_litp__error_in_output(self, mock_run_local_cmd, *_):
        response = Mock()
        response.ok = False
        response.stdout = "ConfigParser.NoSectionError"
        mock_run_local_cmd.return_value = response
        with self.assertRaises(EnvironError) as e:
            self.flow.fetch_password_from_litp()
        self.assertEqual(e.exception.message, "Issue occurred while fetching nas console password from LITP model")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.get_service_status",
           side_effect=["ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_check_status_of_nas__success(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0, 0, 0, 0]
        check_status_of_nas("host", "password")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.get_service_status")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_check_status_of_nas__success_without_retry(self, mock_spawn, mock_status, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0, 0, 0, 0]
        mock_status.side_effect = ["ONLINE"]
        check_status_of_nas("host", "password")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.get_service_status",
           side_effect=["OFFLINE", "ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_check_status_of_nas__lms_login_failed(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [1, 1, 0, 0, 0]
        self.assertRaises(EnvironError, check_status_of_nas, "host", "password")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.get_service_status",
           side_effect=["OFFLINE", "ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_check_status_of_nas__nas_password_prompt_failed(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0]
        self.assertRaises(EnvironError, check_status_of_nas, "host", "password")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.get_service_status",
           side_effect=["OFFLINE", "ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_check_status_of_nas__nas_login_failed(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 1, 0]
        self.assertRaises(EnvironError, check_status_of_nas, "host", "password")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.get_service_status",
           side_effect=["OFFLINE", "ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.retry_status_check", return_value=["OFFLINE", "ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_check_status_of_nas__successful_retry(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0]
        check_status_of_nas("host", "password")

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_execute_nas_command__success_configure(self, mock_spawn, mock_debug):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0]
        execute_nas_command(child, 'cmd', 'configure')
        self.assertEqual(mock_debug.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_execute_nas_command__success_configure_without_prompts(self, mock_spawn, mock_debug):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [1, 1, 0]
        execute_nas_command(child, 'cmd', 'configure')
        self.assertEqual(mock_debug.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_execute_nas_command__success_start(self, mock_spawn, mock_debug):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0]
        execute_nas_command(child, 'cmd', 'start')
        self.assertEqual(mock_debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas",
           side_effect=["OFFLINE", "OFFLINE", "ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_retry_status_check__success(self, mock_spawn, mock_debug, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0, 0, 0, 0]
        retry_status_check(3, 'host', "password")
        self.assertEqual(mock_debug.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.check_status_of_nas",
           side_effect=["ONLINE"])
    @patch("enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02.pexpect.spawn")
    def test_retry_status_check(self, mock_spawn, mock_debug, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1, 0, 0, 0, 0, 0, 0]
        retry_status_check(3, 'host', "password")
        self.assertEqual(mock_debug.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
