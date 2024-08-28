#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from testslib import unit_test_utils

from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.workload.cmexport_18 import CMEXPORT_18


class CmExport18UnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.profile = CMEXPORT_18()
        self.profile.ATTRS = {"EBSTopologyService_schedulerHour": "2", "EBSTopologyService_schedulerMinute": "0"}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_emp_or_ms")
    def test_execute_config_cmd__execute_read_cmd(self, mock_run_cmd, *_):
        mock_response = Mock()
        mock_response.rc = 0
        mock_response.stdout = "50"
        mock_run_cmd.return_value = mock_response
        self.assertEqual("50", self.profile.execute_config_cmd('EBSTopologyService_schedulerHour'))
        mock_run_cmd.assert_called_with(self.profile.BASE_READ_CMD.format("EBSTopologyService_schedulerHour"))

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_emp_or_ms")
    def test_execute_config_cmd__execute_update_cmd(self, mock_run_cmd, *_):
        mock_response = Mock()
        mock_response.rc = 0
        mock_response.stdout = "50"
        mock_run_cmd.return_value = mock_response
        self.assertEqual("50", self.profile.execute_config_cmd('EBSTopologyService_schedulerHour', target_value="50"))
        mock_run_cmd.assert_called_with(self.profile.BASE_UPDATE_CMD.format("EBSTopologyService_schedulerHour", "50"))

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_pod_hostnames_in_cloud_native")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_emp_or_ms")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    def test_execute_config_cmd__execute_update_cmd_cn(self, mock_run_cmd, *_):
        mock_response = Mock()
        mock_response.rc = 0
        mock_response.stdout = "50"
        self.profile.EBSTOPOLOGY_PODS = ["pod1", "pod2"]
        mock_run_cmd.return_value = mock_response
        self.profile.execute_config_cmd('EBSTopologyService_schedulerHour', target_value="50")

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_pod_hostnames_in_cloud_native")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd")
    def test_setup__success_for_cn(self, *_):
        self.profile.EBSTOPOLOGY_PODS.extend(["pod1", "pod2"])
        self.profile.setup()

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_pod_hostnames_in_cloud_native",
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd")
    def test_setup__no_ebstopology_pods(self, *_):
        self.assertRaises(EnvironError, self.profile.setup)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.setup")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_emp_or_ms")
    def test_execute_config_cmd__raise_error(self, mock_run_cmd, *_):
        mock_response = Mock()
        mock_response.rc = 1
        mock_response.stdout = "Attribute does not exist."
        mock_run_cmd.return_value = mock_response
        self.assertRaises(EnvironError, self.profile.execute_config_cmd, self.profile.BASE_READ_CMD.format("test"))

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties",
           side_effect=EnvironError)
    def test_setup__service_not_on_deployment(self, *_):
        self.assertRaises(EnvironError, self.profile.setup)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_pod_hostnames_in_cloud_native")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd",
           side_effect=EnvironError)
    def test_setup__read_initial_value_fails(self, *_):
        self.assertRaises(EnvironError, self.profile.setup)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.log.logger.debug")
    def test_setup__successful(self, mock_debug, *_):
        self.profile.setup()
        mock_debug.assert_called_with("Profile setup passed.")
        self.assertEqual(2, len(self.profile.teardown_list))

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_pod_hostnames_in_cloud_native")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd", side_effect=Exception)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.log.logger.debug")
    def test_setup(self, mock_debug, *_):
        self.profile.EBSTOPOLOGY_PODS = ["pod1"]
        self.assertRaises(Exception, self.profile.setup)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.setup")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd",
           return_value="10")
    def test_execute_flow__successful_read_and_update(self, mock_config_cmd, *_):

        self.profile.execute_flow()
        self.assertEqual(4, mock_config_cmd.call_count)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.setup")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.keep_running", side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd",
           side_effect=["2", "0"])
    def test_execute_flow__value_already_set(self, mock_config_cmd, mock_debug, *_):

        self.profile.execute_flow()
        self.assertEqual(2, mock_config_cmd.call_count)
        mock_debug.assert_any_call("Attribute {0} was already set to {1}.".format("EBSTopologyService_schedulerHour", "2"))

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.setup")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.get_values_from_global_properties")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.keep_running", side_effect=[True, False])
    @patch('enmutils.lib.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.execute_config_cmd",
           side_effect=EnvironError("Unexpexted command output."))
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.add_error_as_exception")
    def test_execute_flow__catch_execute_config_cmd_exception(self, mock_add_error, *_):

        self.profile.execute_flow()
        self.assertEqual(2, mock_add_error.call_count)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.setup", side_effect=EnvironError)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow.CmExport18.add_error_as_exception")
    def test_execute_flow__setup_fails(self, mock_add_error, *_):
        self.profile.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
