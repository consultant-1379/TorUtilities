# !/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow import AmosFlow, Amos09Flow
from enmutils_int.lib.workload import amos_09
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class AmosFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = AmosFlow()
        self.flow.SCRIPTING_CLUSTER_IPS = []
        self.flow.IS_CLOUD_NATIVE = None
        self.flow.IS_EMP = None

    def tearDown(self):
        unit_test_utils.tear_down()

    # get_scripting_vms_ips test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_pod_hostnames_in_cloud_native',
           return_value=["general-scripting-7455c785ff-mgpdj"])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_list_of_scripting_service_ips')
    def test_get_scripting_vms_ips__on_cloud_native_success(self, mock_get_list_of_scripting_service_ips,
                                                            mock_get_pod_hostnames_in_cloud_native, mock_debug_log, *_):
        self.flow.IS_CLOUD_NATIVE = True
        self.assertEqual(["general-scripting-7455c785ff-mgpdj"], self.flow.get_scripting_vms_ips())
        mock_get_pod_hostnames_in_cloud_native.assert_called_with("general-scripting")
        self.assertFalse(mock_get_list_of_scripting_service_ips.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_list_of_scripting_service_ips')
    def test_get_scripting_vms_ips__empty_list_on_cloud_native(self, mock_get_list_of_scripting_service_ips,
                                                               mock_get_pod_hostnames_in_cloud_native,
                                                               mock_debug_log, *_):
        self.flow.IS_CLOUD_NATIVE = True
        mock_get_pod_hostnames_in_cloud_native.return_value = []
        self.assertEqual([], self.flow.get_scripting_vms_ips())
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertFalse(mock_get_list_of_scripting_service_ips.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_list_of_scripting_service_ips')
    def test_get_scripting_vms_ips__fetching_ips_from_global_properties(
            self, mock_get_list_of_scripting_service_ips, mock_get_pod_hostnames_in_cloud_native, mock_debug_log, *_):
        self.flow.IS_CLOUD_NATIVE = False
        mock_get_list_of_scripting_service_ips.return_value = [unit_test_utils.generate_configurable_ip()]
        self.flow.get_scripting_vms_ips()
        self.assertTrue(mock_get_list_of_scripting_service_ips.called)
        self.assertFalse(mock_get_pod_hostnames_in_cloud_native.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_list_of_scripting_service_ips')
    def test_get_scripting_vms_ips__empty_list_while_fetching_ips_from_global_properties(
            self, mock_get_list_of_scripting_service_ips, mock_get_pod_hostnames_in_cloud_native, mock_debug_log, *_):
        self.flow.IS_CLOUD_NATIVE = False
        mock_get_list_of_scripting_service_ips.return_value = []
        self.assertEqual([], self.flow.get_scripting_vms_ips())
        self.assertTrue(mock_get_list_of_scripting_service_ips.called)
        self.assertFalse(mock_get_pod_hostnames_in_cloud_native.called)
        self.assertEqual(mock_debug_log.call_count, 2)

    # adjust_amos_crontab_file test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_adjust_amos_crontab_file__raises_exception(self, mock_run_local_cmd, mock_debug_log, mock_debug_info, *_):
        response = Mock()
        response.rc = 2
        mock_run_local_cmd.return_value = response
        self.assertRaises(EnvironError, self.flow.adjust_minute_field_in_amos_logs_cronjob_file_per_vm, 5)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_debug_info.call_count, 0)

    @patch('__builtin__.open')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.join')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_internal_file_path_for_import')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_adjust_amos_crontab_file__success(self, mock_run_local_cmd, mock_debug, mock_debug_info, *_):
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.return_value = response
        self.flow.adjust_minute_field_in_amos_logs_cronjob_file_per_vm((23, 30))
        self.assertEqual(mock_debug.call_count, 4)
        self.assertEqual(mock_debug_info.call_count, 1)

    # transfer_amos_logs_cron_job_from_workload_vm test cases
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Command")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_transfer_amos_logs_cron_job_from_workload_vm__to_cloud_emp_raises_exception(
            self, mock_run_local_cmd, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        mock_run_local_cmd.side_effect = RuntimeError("Failed to transfer AMOS logs cronjob from Workload VM to emp.")
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        self.assertRaises(EnvironError, self.flow.transfer_amos_logs_cron_job_from_workload_vm)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Command")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_transfer_amos_logs_cron_job_from_workload_vm__to_ms_raises_exception(
            self, mock_run_local_cmd, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        mock_run_local_cmd.side_effect = RuntimeError("Failed to transfer AMOS logs cronjob from Workload VM to MS.")
        self.assertRaises(EnvironError, self.flow.transfer_amos_logs_cron_job_from_workload_vm)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Command")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_transfer_amos_logs_cron_job_from_workload_vm__fail(
            self, mock_run_local_cmd, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 2
        mock_run_local_cmd.return_value = response
        self.assertRaises(Exception, self.flow.transfer_amos_logs_cron_job_from_workload_vm)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Command")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_transfer_amos_logs_cron_job_from_workload_vm__is_successful_on_physical(
            self, mock_run_local_cmd, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.return_value = response
        self.flow.transfer_amos_logs_cron_job_from_workload_vm()
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_info_log.call_count)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Command")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_transfer_amos_logs_cron_job_from_workload_vm__is_successful_on_cloud(
            self, mock_run_local_cmd, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.return_value = response
        self.flow.transfer_amos_logs_cron_job_from_workload_vm()
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_info_log.call_count)
        self.assertEqual(1, mock_run_local_cmd.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Command")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_transfer_amos_logs_cron_job_from_workload_vm__is_successful_on_cloud_native(
            self, mock_run_local_cmd, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        response = Mock()
        response.rc = 0
        mock_copy_file_between_wlvm_and_cloud_native_pod.return_value = response
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = True
        self.flow.transfer_amos_logs_cron_job_from_workload_vm()
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_info_log.call_count)
        self.assertEqual(0, mock_run_local_cmd.call_count)
        self.assertTrue(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    # transfer_amos_logs_cron_job_to_scripting_vms test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__on_enm_cloud_raises_exception(
            self, mock_run_cmd_on_vm, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        mock_run_cmd_on_vm.side_effect = EnvironError("Failed to SSH onto amos/scripting vm.")
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        self.assertRaises(EnvironError, self.flow.transfer_amos_logs_cron_job_to_scripting_vms,
                          unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__on_enm_cloud_successful(
            self, mock_run_cmd_on_vm, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_vm.return_value = response
        self.flow.transfer_amos_logs_cron_job_to_scripting_vms(unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_info_log.call_count)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__on_physical_raises_exception(
            self, mock_run_cmd_on_ms, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        mock_run_cmd_on_ms.side_effect = EnvironError("Failed to SSH onto amos/scripting vm.")
        self.assertRaises(EnvironError, self.flow.transfer_amos_logs_cron_job_to_scripting_vms,
                          unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__fail_on_physical(
            self, mock_run_cmd_on_ms, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 2
        mock_run_cmd_on_ms.return_value = response
        self.assertRaises(Exception, self.flow.transfer_amos_logs_cron_job_to_scripting_vms,
                          unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__is_successful_on_physical(
            self, mock_run_cmd_on_ms, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_and_cloud_native_pod,
            *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_ms.return_value = response
        self.flow.transfer_amos_logs_cron_job_to_scripting_vms(unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_info_log.call_count)
        self.assertEqual(1, mock_run_cmd_on_ms.call_count)
        self.assertFalse(mock_copy_file_between_wlvm_and_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__on_cloud_native_raises_exception(
            self, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_cn_pod, *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = True
        mock_copy_file_between_wlvm_cn_pod.side_effect = EnvironError("Failed to SSH onto amos/scripting vm.")
        self.assertRaises(EnvironError, self.flow.transfer_amos_logs_cron_job_to_scripting_vms,
                          "general-scripting-7455c785ff-mgpdj")
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_info_log.call_count)
        self.assertTrue(mock_copy_file_between_wlvm_cn_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.'
           'copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.info')
    def test_transfer_amos_logs_cron_job_to_scripting_vms__is_successful_on_cloud_native(
            self, mock_info_log, mock_debug_log, mock_copy_file_between_wlvm_cn_pod, *_):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = True
        response = Mock()
        response.rc = 0
        mock_copy_file_between_wlvm_cn_pod.return_value = response
        self.flow.transfer_amos_logs_cron_job_to_scripting_vms("general-scripting-7455c785ff-mgpdj")
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_info_log.call_count)
        self.assertTrue(mock_copy_file_between_wlvm_cn_pod.called)

    # copy_amos_cron_job_into_cron_folder test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_copy_amos_cron_job_into_vm_cron_folder__on_enm_cloud_raises_exception(
            self, mock_run_cmd_on_vm, mock_run_cmd_on_cloud_native_pod, mock_debug_log):
        mock_run_cmd_on_vm.side_effect = EnvironError("Failed to copy amos logs crontab file to crontab file directory .")
        self.flow.IS_CLOUD_NATIVE = False
        self.assertRaises(EnvironError, self.flow.copy_amos_cron_job_into_cron_folder,
                          unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(0, mock_run_cmd_on_cloud_native_pod.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_copy_amos_cron_job_into_vm_cron_folder__on_physical_raises_exception(
            self, mock_run_cmd_on_vm, mock_run_cmd_on_cloud_native_pod, mock_debug_log):
        mock_run_cmd_on_vm.side_effect = EnvironError("Failed to SSH onto amos/scripting vm.")
        self.flow.IS_CLOUD_NATIVE = False
        self.assertRaises(EnvironError, self.flow.copy_amos_cron_job_into_cron_folder,
                          unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(0, mock_run_cmd_on_cloud_native_pod.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_copy_amos_cron_job_into_vm_cron_folder__fail(
            self, mock_run_cmd_on_vm, mock_run_cmd_on_cloud_native_pod, mock_debug_log):
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 2
        mock_run_cmd_on_vm.return_value = response
        self.assertRaises(Exception, self.flow.copy_amos_cron_job_into_cron_folder,
                          unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(0, mock_run_cmd_on_cloud_native_pod.call_count)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_copy_amos_cron_job_into_cron_folder__is_successful_on_physical(
            self, mock_run_cmd_on_vm, mock_run_cmd_on_cloud_native_pod, mock_debug_log):
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_vm.return_value = response
        self.flow.copy_amos_cron_job_into_cron_folder(unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(0, mock_run_cmd_on_cloud_native_pod.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_copy_amos_cron_job_into_cron_folder__is_successful_on_cloud(
            self, mock_run_cmd_on_vm, mock_run_cmd_on_cloud_native_pod, mock_debug_log):
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_vm.return_value = response
        self.flow.copy_amos_cron_job_into_cron_folder(unit_test_utils.generate_configurable_ip())
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(0, mock_run_cmd_on_cloud_native_pod.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_copy_amos_cron_job_into_cron_folder__is_successful_on_cloud_native(
            self, mock_run_cmd_on_vm, mock_run_cmd_on_cloud_native_pod, mock_debug_log):
        self.flow.IS_CLOUD_NATIVE = True
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_cloud_native_pod.return_value = response
        self.flow.copy_amos_cron_job_into_cron_folder("general-scripting-7455c785ff-mgpdj")
        self.assertEqual(0, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_run_cmd_on_cloud_native_pod.call_count)
        self.assertEqual(2, mock_debug_log.call_count)

    # remove_amos_logs_crontab_file test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_enm_cloud_WLVM_raises_exception(self, mock_run_local_cmd,
                                                                               mock_run_cmd_on_ms,
                                                                               mock_run_cmd_on_vm,
                                                                               mock_run_cmd_on_cloud_native_pod,
                                                                               mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        mock_run_local_cmd.side_effect = RuntimeError("Failed to remove AMOS LOGS CRONTAB file from Workload VM.")
        self.assertRaises(RuntimeError, self.flow.remove_amos_logs_crontab_file)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertFalse(mock_run_cmd_on_ms.called)
        self.assertFalse(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_physical_WLVM_raises_exception(self, mock_run_local_cmd,
                                                                              mock_run_cmd_on_ms,
                                                                              mock_run_cmd_on_vm,
                                                                              mock_run_cmd_on_cloud_native_pod,
                                                                              mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        mock_run_local_cmd.side_effect = RuntimeError("Failed to remove AMOS LOGS CRONTAB file from Workload VM.")
        self.assertRaises(RuntimeError, self.flow.remove_amos_logs_crontab_file)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertFalse(mock_run_cmd_on_ms.called)
        self.assertFalse(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_enm_cloud_emp_raises_exception(self, mock_run_local_cmd,
                                                                              mock_run_cmd_on_ms,
                                                                              mock_run_cmd_on_vm,
                                                                              mock_run_cmd_on_cloud_native_pod,
                                                                              mock_mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        mock_run_cmd_on_vm.side_effect = RuntimeError("Failed to remove AMOS LOGS CRONTAB file from EMP.")
        self.assertRaises(RuntimeError, self.flow.remove_amos_logs_crontab_file)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertFalse(mock_run_cmd_on_ms.called)
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(1, mock_mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_enm_cloud_emp_success(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                                     mock_run_cmd_on_vm,
                                                                     mock_run_cmd_on_cloud_native_pod,
                                                                     mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        self.flow.IS_EMP = True
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_vm.return_value = response
        mock_run_local_cmd.return_value = response
        self.flow.remove_amos_logs_crontab_file()
        self.assertTrue(mock_run_local_cmd.called)
        self.assertFalse(mock_run_cmd_on_ms.called)
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_enm_physical_success(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                                    mock_run_cmd_on_vm,
                                                                    mock_run_cmd_on_cloud_native_pod,
                                                                    mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.return_value = response
        mock_run_cmd_on_ms.return_value, mock_run_cmd_on_vm.return_value = response, response
        self.flow.remove_amos_logs_crontab_file()
        self.assertTrue(mock_run_local_cmd.called)
        self.assertTrue(mock_run_cmd_on_ms.called)
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_enm_physical_fail(self, mock_run_local_cmd, mock_run_cmd_on_ms,
                                                                 mock_run_cmd_on_vm,
                                                                 mock_run_cmd_on_cloud_native_pod,
                                                                 mock_debug_log):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        response = Mock()
        response.rc = 2
        mock_run_cmd_on_vm.return_value = response
        self.assertRaises(Exception, self.flow.remove_amos_logs_crontab_file)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertTrue(mock_run_cmd_on_ms.called)
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_enm_physical_ms_raises_exception(self, mock_run_local_cmd,
                                                                                mock_run_cmd_on_ms, mock_run_cmd_on_vm,
                                                                                mock_run_cmd_on_cloud_native_pod,
                                                                                mock_debug_log):
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = False
        self.flow.SCRIPTING_CLUSTER_IPS = [unit_test_utils.generate_configurable_ip(),
                                           unit_test_utils.generate_configurable_ip()]
        mock_run_cmd_on_vm.side_effect = RuntimeError("Failed to remove AMOS LOGS CRONTAB file from EMP.")
        self.assertRaises(RuntimeError, self.flow.remove_amos_logs_crontab_file)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertTrue(mock_run_cmd_on_ms.called)
        self.assertTrue(mock_run_cmd_on_vm.called)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_cloud_native_success(self, mock_run_local_cmd,
                                                                    mock_run_cmd_on_ms, mock_run_cmd_on_vm,
                                                                    mock_run_cmd_on_cloud_native_pod,
                                                                    mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = ["general-scripting-7455c785ff-mgpdj"]
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = True
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_cloud_native_pod.return_value, mock_run_local_cmd.return_value = response, response
        self.flow.remove_amos_logs_crontab_file()
        self.assertTrue(mock_run_local_cmd.called)
        self.assertFalse(mock_run_cmd_on_ms.called)
        self.assertFalse(mock_run_cmd_on_vm.called)
        self.assertTrue(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_ms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_local_cmd')
    def test_remove_amos_logs_crontab_file__on_cloud_native_fail(self, mock_run_local_cmd,
                                                                 mock_run_cmd_on_ms, mock_run_cmd_on_vm,
                                                                 mock_run_cmd_on_cloud_native_pod,
                                                                 mock_debug_log):
        self.flow.SCRIPTING_CLUSTER_IPS = ["general-scripting-7455c785ff-mgpdj"]
        self.flow.IS_EMP = False
        self.flow.IS_CLOUD_NATIVE = True
        response = Mock()
        response.rc = 0
        mock_run_local_cmd.return_value = response
        mock_run_cmd_on_cloud_native_pod.return_value = Mock(rc=2)
        self.assertRaises(Exception, self.flow.remove_amos_logs_crontab_file)
        self.assertTrue(mock_run_local_cmd.called)
        self.assertFalse(mock_run_cmd_on_ms.called)
        self.assertFalse(mock_run_cmd_on_vm.called)
        self.assertTrue(mock_run_cmd_on_cloud_native_pod.called)
        self.assertEqual(1, mock_debug_log.call_count)

    # set_teardown_objects test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.delete')
    def test_set_teardown_objects__appends_callables_to_list(self, mock_instance_object):
        self.flow.set_teardown_objects(mock_instance_object)
        for item in self.flow.teardown_list:
            self.assertTrue(callable(item))

    # change_cron_job_file_permissions test cases
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_change_cron_job_file_permissions__successful_on_physical(self, mock_run_cmd_on_vm, mock_debug,
                                                                      mock_run_cmd_on_cloud_native_pod):
        ip = generate_configurable_ip()
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_vm.return_value = response
        self.flow.change_cron_job_file_permissions(ip)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug.call_count)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_change_cron_job_file_permissions__fails_on_physical(self, mock_run_cmd_on_vm, mock_debug,
                                                                 mock_run_cmd_on_cloud_native_pod):
        ip = generate_configurable_ip()
        self.flow.IS_CLOUD_NATIVE = False
        response = Mock()
        response.rc = 2
        mock_run_cmd_on_vm.return_value = response
        self.assertRaises(Exception, self.flow.change_cron_job_file_permissions, ip)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug.call_count)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_change_cron_job_file_permissions__successful_on_cloud_native(self, mock_run_cmd_on_vm, mock_debug,
                                                                          mock_run_cmd_on_cloud_native_pod):
        scripting_pod_host_name = "general-scripting-7455c785ff-mgpdj"
        self.flow.IS_CLOUD_NATIVE = True
        response = Mock()
        response.rc = 0
        mock_run_cmd_on_cloud_native_pod.return_value = response
        self.flow.change_cron_job_file_permissions(scripting_pod_host_name)
        self.assertEqual(0, mock_run_cmd_on_vm.call_count)
        self.assertEqual(2, mock_debug.call_count)
        self.assertTrue(mock_run_cmd_on_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_change_cron_job_file_permissions__exception_on_cloud_native(self, mock_run_cmd_on_vm, mock_debug,
                                                                         mock_run_cmd_on_cloud_native_pod):
        scripting_pod_host_name = "general-scripting-7455c785ff-mgpdj"
        self.flow.IS_CLOUD_NATIVE = True
        response = Mock()
        response.rc = 2
        mock_run_cmd_on_cloud_native_pod.return_value = response
        self.assertRaises(Exception, self.flow.change_cron_job_file_permissions, scripting_pod_host_name)
        self.assertEqual(0, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug.call_count)
        self.assertTrue(mock_run_cmd_on_cloud_native_pod.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.run_cmd_on_vm')
    def test_change_cron_job_file_permissions__raise_env_error_on_cloud_native(self, mock_run_cmd_on_vm, mock_debug,
                                                                               mock_run_cmd_on_cloud_native_pod):
        scripting_pod_host_name = "general-scripting-7455c785ff-mgpdj"
        mock_run_cmd_on_cloud_native_pod.side_effect = Exception("something is wrong")
        self.assertRaises(EnvironError, self.flow.change_cron_job_file_permissions, scripting_pod_host_name)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)
        self.assertEqual(1, mock_debug.call_count)
        self.assertFalse(mock_run_cmd_on_cloud_native_pod.called)


class Amos09FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Amos09Flow()
        self.amos_09 = amos_09.AMOS_09()
        self.exception = Exception("Some Exception")
        self.flow.SCRIPTING_CLUSTER_IPS = []
        self.flow.IS_CLOUD_NATIVE = None
        self.flow.IS_EMP = None
        self.flow.SCHEDULE_SLEEP = 60

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.execute_flow')
    def test_run__in_amos_09_is_successful(self, mock_execute_flow):
        self.amos_09.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.get_scripting_vms_ips',
           return_value=["general-scripting-7455c785ff-mgpdj", "general-scripting-1255c785ff-mgpdj"])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_enm_on_cloud_native',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_enm_on_cloud_native',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_emp', return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.perform_iteration_actions')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.set_teardown_objects')
    def test_execute_flow__is_successful_on_cloud_native(self, mock_set_teardown_objects,
                                                         mock_perform_iteration_actions, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_set_teardown_objects.called)
        self.assertEqual(mock_perform_iteration_actions.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.perform_iteration_actions')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_enm_on_cloud_native',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.set_teardown_objects')
    def test_execute_flow__is_successful_on_cloud(self, mock_set_teardown_objects, mock_perform_iteration_actions, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_set_teardown_objects.called)
        self.assertEqual(mock_perform_iteration_actions.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.perform_iteration_actions')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_enm_on_cloud_native',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_emp', return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.set_teardown_objects')
    def test_execute_flow__is_successful_on_physical(self, mock_set_teardown_objects, mock_perform_iteration_actions,
                                                     *_):
        self.flow.execute_flow()
        self.assertTrue(mock_set_teardown_objects.called)
        self.assertEqual(mock_perform_iteration_actions.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_enm_on_cloud_native',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.is_emp', return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.perform_iteration_actions')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.add_error_as_exception')
    def test_execute_flow__raises_exception(self, mock_add_error, mock_set_teardown_objects,
                                            mock_perform_iteration_actions, *_):
        mock_perform_iteration_actions.side_effect = [EnvironError]
        self.flow.execute_flow()
        self.assertTrue(mock_set_teardown_objects.called)
        self.assertEqual(mock_perform_iteration_actions.call_count, 1)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.get_scripting_vms_ips',
           return_value=[unit_test_utils.generate_configurable_ip(), unit_test_utils.generate_configurable_ip()])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'script_execution_amos_log_cleanup')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'set_key_location')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'adjust_minute_field_in_amos_logs_cronjob_file_per_vm', side_effect=[EnvironError('Error'), None])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'change_cron_job_file_permissions')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'copy_amos_cron_job_into_cron_folder')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'transfer_amos_logs_cron_job_to_scripting_vms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'transfer_amos_logs_cron_job_from_workload_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.add_error_as_exception')
    def test_perform_iteration_actions__continues_with_errors(self, mock_add_error_as_exception,
                                                              mock_transfer_amos_logs,
                                                              mock_transfer_amos_logs_cron_job_to_scripting_vms,
                                                              mock_copy_amos_cron_job_into_cron_folder,
                                                              mock_change_cron_job_file_permissions, *_):
        self.flow.perform_iteration_actions()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_transfer_amos_logs.called)
        self.assertTrue(mock_transfer_amos_logs_cron_job_to_scripting_vms.called)
        self.assertTrue(mock_copy_amos_cron_job_into_cron_folder.called)
        self.assertTrue(mock_change_cron_job_file_permissions.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.get_scripting_vms_ips',
           return_value=[unit_test_utils.generate_configurable_ip(), unit_test_utils.generate_configurable_ip()])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'script_execution_amos_log_cleanup')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'set_key_location')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'change_cron_job_file_permissions')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'copy_amos_cron_job_into_cron_folder')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'transfer_amos_logs_cron_job_to_scripting_vms')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'transfer_amos_logs_cron_job_from_workload_vm')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.add_error_as_exception')
    def test_perform_iteration_actions__is_successful(self, mock_add_error_as_exception,
                                                      mock_transfer_amos_logs,
                                                      mock_transfer_amos_logs_cron_job_to_scripting_vms,
                                                      mock_copy_amos_cron_job_into_cron_folder,
                                                      mock_change_cron_job_file_permissions, *_):
        with patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
                   'adjust_minute_field_in_amos_logs_cronjob_file_per_vm') as mock_adjust_min_field_amos_logs_cronjob_file_per_vm:
            self.flow.perform_iteration_actions()
            mock_adjust_min_field_amos_logs_cronjob_file_per_vm.assert_called_with((0, 0))
            self.assertFalse(mock_add_error_as_exception.called)
            self.assertTrue(mock_transfer_amos_logs.called)
            self.assertTrue(mock_transfer_amos_logs_cron_job_to_scripting_vms.called)
            self.assertTrue(mock_copy_amos_cron_job_into_cron_folder.called)
            self.assertTrue(mock_change_cron_job_file_permissions.called)

    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.AmosFlow.remove_amos_logs_crontab_file')
    def test_delete__is_success(self, mock_debug, *_):
        self.flow.delete()
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.filesystem.does_file_exist", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.add_error_as_exception")
    def test_set_key_location__errors_on_no_key(self, mock_handler, *_):
        self.flow.is_cloud = True
        self.flow.set_key_location()
        self.assertEqual(mock_handler.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.filesystem.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=True)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.add_error_as_exception")
    def test_set_key_location__success_cloud(self, mock_handler, *_):
        self.flow.set_key_location()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.filesystem.does_file_exist", return_value=True)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.add_error_as_exception")
    def test_set_key_location__success_physical(self, mock_handler, *_):
        self.flow.set_key_location()
        self.assertEqual(mock_handler.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.set_key_location')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'amos_log_cleanup_script_cloud_and_physical')
    def test_script_execution_amos_log_cleanup__success_physical(self, mock_cloud_and_physical, *_):
        self.flow.script_execution_amos_log_cleanup("192.300.108.72")
        self.assertTrue(mock_cloud_and_physical.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__success_physical(self, mock_send, *_):
        self.flow.amos_log_cleanup_script_cloud_and_physical("192.300.108.72")
        self.assertEqual(11, mock_send.call_count)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_root_user(self, mock_send, *_):
        self.assertRaises(EnvironError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_script_file_execution(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_setting_value_C(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_giving_option_R(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_setting_normal_commands(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_setting_heavy_commands(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_giving_option_S(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_setting_hour_value(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_setting_minute_value(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_giving_option_Q(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', side_effect=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    def test_amos_log_cleanup_script_cloud_and_physical__failure_physical_at_final_step(self, mock_send, *_):
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "192.300.108.72")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_connecting_pod(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.return_value = 1
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnvironError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_script_file_execution(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_setting_value_C(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_giving_option_R(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_setting_normal_commands(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_setting_heavy_commands(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_giving_option_S(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_setting_hour_value(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_setting_minute_value(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_giving_option_Q(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__failure_cloudnative_at_final_step(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.side_effect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        self.flow.IS_CLOUD_NATIVE = True
        self.assertRaises(EnmApplicationError, self.flow.script_execution_amos_log_cleanup, "general-scripting-0")

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.Amos09Flow.'
           'amos_log_cleanup_script_cloudnative')
    def test_script_execution_amos_log_cleanup__success_cloudnative(self, mock_cloudnative, *_):
        self.flow.IS_CLOUD_NATIVE = True
        self.flow.script_execution_amos_log_cleanup("general-scripting-0")
        self.assertTrue(mock_cloudnative.called)

    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.config.is_a_cloud_deployment", return_value=False)
    @patch("enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.get_enm_cloud_native_namespace")
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.expect', return_value=0)
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn.sendline')
    @patch('enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow.pexpect.spawn')
    def test_amos_log_cleanup_script_cloudnative__success_cloudnative(self, mock_spawn, *_):
        child = mock_spawn.return_value.__enter__.return_value
        child.expect.return_value = 0
        self.flow.IS_CLOUD_NATIVE = True
        self.flow.amos_log_cleanup_script_cloudnative("kubectl -n enm2 exec -it general-scripting-0 -- bash",
                                                      "general-scripting-0")

if __name__ == "__main__":
    unittest2.main(verbosity=2)
