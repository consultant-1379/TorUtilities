#!/usr/bin/env python
import unittest2
from mock import patch, PropertyMock, Mock

from enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow import CliMon03Flow, CliMon01Flow
from enmutils_int.lib.workload.cli_mon_01 import CLI_MON_01
from enmutils_int.lib.workload.cli_mon_03 import CLI_MON_03
from testslib import unit_test_utils

SUCCESS_RESPONSE = """
  svc_cluster                          Grp_mscmip  svc-2      standalone           vm        ONLINE          OK       -
  svc_cluster                     Grp_haproxy_int  svc-2  active-standby          lsb       OFFLINE          OK       -
  svc_cluster                     Grp_haproxy_int  svc-1  active-standby          lsb        ONLINE          OK       -

ENM VCS llt heartbeat healthcheck Status: PASSED
Successfully Completed VCS LLT Heartbeat Healthcheck
-----------------------------------------------------------------
Successfully Completed ENM System Healthcheck
-----------------------------------------------------------------
        """
FAILURE_RESPONSE = """
  svc_cluster                          Grp_mscmip  svc-2      standalone           vm        ONLINE          OK       -
  svc_cluster                     Grp_haproxy_int  svc-2  active-standby          lsb
  OFFLINE          OK       -
  svc_cluster                     Grp_haproxy_int  svc-1  active-standby          lsb        ONLINE          OK       -

ENM VCS llt heartbeat healthcheck Status: PASSED
Successfully Completed VCS LLT Heartbeat Healthcheck
-----------------------------------------------------------------
ENM System Healthcheck errors!
-----------------------------------------------------------------
        """


class CliMon01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CliMon01Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.verify_health_check_response')
    def test_execute_flow__success(self, mock_verify, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_verify.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.'
           'verify_health_check_response_on_cloud_native')
    def test_execute_flow__success_cloud_native(self, mock_verify_cloud_native, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_verify_cloud_native.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.verify_health_check_response',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.add_error_as_exception')
    def test_execute_flow__adds_exception(self, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.'
           'verify_health_check_response_on_cloud_native', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.add_error_as_exception')
    def test_execute_flow__cloud_native_adds_exception(self, mock_error, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.get_enm_cloud_native_namespace', return_value="namespace")
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.get_pod_hostnames_in_cloud_native', return_value=["pod", "pod1"])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.run_cmd_on_cloud_native_pod')
    def test_verify_health_check_response_on_cloud_native__success(self, mock_run, mock_error, *_):
        response = Mock()
        response.stdout = "Str\nStr1"
        mock_run.return_value = response
        self.flow.verify_health_check_response_on_cloud_native()
        self.assertEqual(0, mock_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.get_enm_cloud_native_namespace',
           return_value="namespace")
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.get_pod_hostnames_in_cloud_native',
           return_value=["pod", "pod1"])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.run_cmd_on_cloud_native_pod')
    def test_verify_health_check_response_on_cloud_native__exception(self, mock_run, mock_error, *_):
        response = Mock()
        response.stdout = "Str\nHealth check failed."
        mock_run.return_value = response
        self.flow.verify_health_check_response_on_cloud_native()
        self.assertEqual(1, mock_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.Command')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.run_cmd_on_ms')
    def test_execute_system_health_check__returns_response(self, mock_run, _):
        response = Mock()
        response.stdout = "Str\nStr1"
        mock_run.return_value = response
        result = self.flow.execute_system_health_check()
        self.assertEqual(2, len(result))

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.check_for_active_litp_plan', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.execute_system_health_check',
           return_value=SUCCESS_RESPONSE.split('\n'))
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.add_error_as_exception')
    def test_verify_health_check_response__success(self, mock_add_error, *_):
        self.flow.verify_health_check_response()
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.check_for_active_litp_plan', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.execute_system_health_check',
           return_value=FAILURE_RESPONSE.split('\n'))
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.add_error_as_exception')
    def test_verify_health_check_response__failure(self, mock_add_error, *_):
        self.flow.verify_health_check_response()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.check_for_active_litp_plan', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.execute_system_health_check')
    def test_verify_health_check_response__does_not_execute_if_litp_plan(self, mock_execute, *_):
        self.flow.verify_health_check_response()
        self.assertEqual(0, mock_execute.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon01Flow.execute_flow')
    def test_cli_mon_01__run(self, mock_execute):
        cli_mon_01_profile = CLI_MON_01()
        cli_mon_01_profile.run()
        self.assertEqual(1, mock_execute.call_count)


class CliMon03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CliMon03Flow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.Command')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.run_local_cmd')
    def test_execute_flow__success(self, mock_run, *_):
        response = Mock()
        response.rc = 0
        mock_run.return_value = response
        self.flow.execute_flow()
        self.assertEqual(1, mock_run.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.Command')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.run_local_cmd')
    def test_execute_flow__adds_error(self, mock_run, mock_add, *_):
        response = Mock()
        response.rc = 127
        mock_run.return_value = response
        self.flow.execute_flow()
        self.assertEqual(1, mock_run.call_count)
        self.assertEqual(1, mock_add.call_count)

    @patch('enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow.CliMon03Flow.execute_flow')
    def test_cli_mon_03__run(self, mock_execute):
        cli_mon_03_profile = CLI_MON_03()
        cli_mon_03_profile.run()
        self.assertEqual(1, mock_execute.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
