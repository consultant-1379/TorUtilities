#!/usr/bin/env python
from datetime import datetime
import subprocess
from testslib import unit_test_utils
import unittest2
from mock import patch, Mock, PropertyMock, call
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.fs_quotas_flows import fs_quotas_flow
from enmutils_int.lib.workload import fs_quotas_01


class FsQuotas01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="cephtest")
        self.profile = fs_quotas_flow.FsQuotas01Flow()
        self.profile.user = self.user
        self.profile.USER_ROLES = ["Scripting_Operator", "SECURITY_ADMIN"]
        self.profile.NUM_USERS = 1
        self.profile.CEPH_QUOTA_LIMIT = 300
        self.profile.FILE_SIZE = "150M"
        self.profile.USER_NAME = "cephtest_1"
        self.profile.SCHEDULED_DAYS = ["THURSDAY"]
        self.profile.SCHEDULED_TIMES_STRINGS = ['11:30:00']
        self.profile.RUN_UNTIL = "12.30:00"

    @classmethod
    def setUpClass(cls):
        cls.bad_command_result = subprocess.CalledProcessError(returncode=2, cmd=["bad"], output="some_output")

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "get_enm_cloud_native_namespace", return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "sleep_until_day", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "get_pod_info_in_cenm", return_value=["cephfs-quotas-controller"])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "verify_whether_deployment_type_is_cnis")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "perform_fs_quotas_operations")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "create_custom_user_in_enm")
    def test_execute_flow__is_successful(self, mock_create_users, mock_perform_fs_quotas_operations, *_):
        mock_create_users.return_value = [Mock(username="test", password="test")]
        self.profile.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertEqual(mock_perform_fs_quotas_operations.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "get_enm_cloud_native_namespace", return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "sleep_until_day", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "get_pod_info_in_cenm", return_value=["cephfs-quotas-controller"])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "verify_whether_deployment_type_is_cnis")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "perform_fs_quotas_operations")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "create_custom_user_in_enm")
    def test_execute_flow__raises_environ_error(self, mock_create_users, mock_perform_fs_quotas_operations,
                                                mock_add_error, *_):
        self.profile.execute_flow()
        self.assertFalse(mock_create_users.called)
        self.assertEqual(mock_perform_fs_quotas_operations.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "get_enm_cloud_native_namespace", return_value="cenm168")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "sleep_until_day", return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "keep_running", side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow."
           "get_pod_info_in_cenm", return_value=["cephfs-quotas-controller"])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "verify_whether_deployment_type_is_cnis", return_value=False)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "perform_fs_quotas_operations")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "create_custom_user_in_enm")
    def test_execute_flow__if_deployment_is_non_cnis(self, mock_create_users, mock_perform_fs_quotas_operations,
                                                     mock_add_error, *_):
        self.profile.execute_flow()
        self.assertFalse(mock_create_users.called)
        self.assertEqual(mock_perform_fs_quotas_operations.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 0)

    # disable_ceph_quota_for_user test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.update_ceph_quotas_config")
    def test_disable_ceph_quota_for_user__is_successful(self, mock_update_ceph_quotas_config,
                                                        mock_check_profile_memory_usage):
        self.profile.disable_ceph_quota_for_user()
        self.assertEqual(mock_update_ceph_quotas_config.call_count, 1)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    # log_results_of_current_iteration test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_log_results_of_current_iteration__is_successful(self, mock_debug_log):
        self.profile.iteration_success = True
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.log_results_of_current_iteration()
        message = ("cephtest_1 user result for ceph quota limit is working fine as per configuration, "
                   "scripting service ip: 1.1.1.1: port: 5020, RESULT: PASS")
        self.assertTrue(call(message) in mock_debug_log.mock_calls)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_log_results_of_current_iteration__if_iteration_is_fail(self, mock_debug_log):
        self.profile.iteration_success = False
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.log_results_of_current_iteration()
        message = ("cephtest_1 user result for ceph quota limit is not working fine as per configuration, "
                   "scripting service ip: 1.1.1.1: port: 5020, RESULT: FAIL")
        self.assertTrue(call(message) in mock_debug_log.mock_calls)

    # get_ceph_quotas_config test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_get_ceph_quotas_config__is_successful(self, mock_debug_log, mock_check_profile_memory_usage):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "quotaEnabled=true\nsizeGenericQuota=0\ncephtest_1=300"
        self.profile.user.get.return_value = response
        self.profile.get_ceph_quotas_config()
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_get_ceph_quotas_config__if_fail(self, mock_debug_log, mock_check_profile_memory_usage):
        response = Mock()
        response.ok = True
        response.status_code = 204
        response.text = ""
        self.profile.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.profile.get_ceph_quotas_config)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 0)

    def test_create_cephtest_user_in_enm__is_success(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    def test_create_cephtest_user_in_enm__raises_exception_while_creating_user(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    def test_create_cephtest_user_in_enm__raises_enm_application_error(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    # check_ceph_quotas_attributes test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.shell.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_check_ceph_quotas_attributes__is_successful(self, mock_debug_log, mock_run_cmd):
        mock_run_cmd.return_value = Mock(ok=True, stdout=('# file: home/shared/cephtest_1\n'
                                                          'ceph.quota.max_bytes="314572800"'))
        self.profile.check_ceph_quotas_attributes()
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_run_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.shell.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_check_ceph_quotas_attributes__if_user_data_not_found(self, mock_debug_log, mock_run_cmd):
        mock_run_cmd.return_value = Mock(ok=True, stdout="No such attribute")
        self.profile.check_ceph_quotas_attributes()
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_run_cmd.call_count, 1)

    # delete_ceph_user_home_dir test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.verify_and_remove_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.shell.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_delete_ceph_user_home_dir__is_successful(self, mock_debug_log, mock_run_cmd, check_profile_memory_usage,
                                                      mock_verify_and_remove_ssh_keys):
        mock_run_cmd.return_value = Mock(rc=0)
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.delete_ceph_user_home_dir()
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_run_cmd.call_count, 1)
        self.assertEqual(mock_verify_and_remove_ssh_keys.call_count, 1)
        self.assertEqual(check_profile_memory_usage.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.verify_and_remove_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.shell.run_cmd_on_cloud_native_pod")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_delete_ceph_user_home_dir__fail_to_delete_user(self, mock_debug_log, mock_run_cmd,
                                                            check_profile_memory_usage, mock_verify_and_remove_ssh_keys):
        mock_run_cmd.return_value = Mock(rc=1)
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.delete_ceph_user_home_dir()
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_run_cmd.call_count, 1)
        self.assertEqual(mock_verify_and_remove_ssh_keys.call_count, 1)
        self.assertEqual(check_profile_memory_usage.call_count, 1)

    # update_ceph_quotas_config test cases
    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_update_ceph_quotas_config__is_successful(self, mock_debug_log, mock_check_profile_memory_usage, _):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "Data Sent"
        self.profile.user.post.return_value = response
        payload = {"file": "quotaEnabled=true\nsizeGenericQuota=0\ncephtest_1=300"}
        self.profile.update_ceph_quotas_config(payload)
        self.assertEqual(mock_debug_log.call_count, 5)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_update_ceph_quotas_config__failed_to_remove(self, mock_debug_log, mock_check_profile_memory_usage, _):
        response = Mock()
        response.ok = True
        response.status_code = 204
        response.text = ""
        self.profile.user.post.return_value = response
        payload = {"file": "quotaEnabled=false\nsizeGenericQuota=0"}
        self.assertRaises(EnmApplicationError, self.profile.update_ceph_quotas_config, payload, "remove")
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 0)

    # create_dummy_files_for_ceph_user test cases
    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_create_dummy_files_for_ceph_user__is_successful(self, mock_pexpect, mock_debug_log,
                                                             mock_check_profile_memory_usage, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [0, 1, 2, 0, 0, 1]
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.create_dummy_files_for_ceph_user(3)
        self.assertEqual(mock_debug_log.call_count, 11)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_create_dummy_files_for_ceph_user__without_prompt(self, mock_pexpect, mock_debug_log,
                                                              mock_check_profile_memory_usage, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [1, 2, 0, 0, 1]
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.create_dummy_files_for_ceph_user(3)
        self.assertEqual(mock_debug_log.call_count, 10)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_create_dummy_files_for_ceph_user__without_password(self, mock_pexpect, mock_debug_log,
                                                                mock_check_profile_memory_usage, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [2, 0, 0, 1]
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.create_dummy_files_for_ceph_user(3)
        self.assertEqual(mock_debug_log.call_count, 9)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_create_dummy_files_for_ceph_user__without_failed_truncate_message(self, mock_pexpect, mock_debug_log,
                                                                               mock_check_profile_memory_usage, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [2, 0, 0, 0]
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.create_dummy_files_for_ceph_user(3)
        self.assertEqual(mock_debug_log.call_count, 9)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_create_dummy_files_for_ceph_user__if_fail(self, mock_pexpect, mock_debug_log,
                                                       mock_check_profile_memory_usage, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [3]
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.create_dummy_files_for_ceph_user(3)
        self.assertEqual(mock_debug_log.call_count, 0)
        self.assertEqual(mock_check_profile_memory_usage.call_count, 1)

    # login_to_scripting_server_and_create_home_dir test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.verify_and_remove_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_login_to_scripting_server_and_create_home_dir__is_successful(self, mock_pexpect, mock_debug_log,
                                                                          mock_verify_and_remove_ssh_keys):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [0, 1, 2]
        child.before = "Creating directory"
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.profile.login_to_scripting_server_and_create_home_dir()
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_verify_and_remove_ssh_keys.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.verify_and_remove_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_login_to_scripting_server_and_create_home_dir__raises_environ_error(self, mock_pexpect, mock_debug_log,
                                                                                 mock_verify_and_remove_ssh_keys):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [0, 1, 2]
        child.before = "Something"
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.assertRaises(EnvironError, self.profile.login_to_scripting_server_and_create_home_dir)
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_verify_and_remove_ssh_keys.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.verify_and_remove_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_login_to_scripting_server_and_create_home_dir__without_prompt(self, mock_pexpect, mock_debug_log,
                                                                           mock_verify_and_remove_ssh_keys):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [1, 2]
        child.before = "Something"
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.assertRaises(EnvironError, self.profile.login_to_scripting_server_and_create_home_dir)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_verify_and_remove_ssh_keys.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.verify_and_remove_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.pexpect")
    def test_login_to_scripting_server_and_create_home_dir__without_password(self, mock_pexpect, mock_debug_log,
                                                                             mock_verify_and_remove_ssh_keys):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [2]
        child.before = "Something"
        self.profile.currently_used_scripting_service_port = "5020"
        self.profile.scripting_service_ip_list = ['1.1.1.1']
        self.assertRaises(EnvironError, self.profile.login_to_scripting_server_and_create_home_dir)
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_verify_and_remove_ssh_keys.call_count, 1)

    # perform_fs_quotas_operations test cases
    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.get_list_of_scripting_service_ips",
           return_value=['1.1.1.1'])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.disable_ceph_quota_for_user")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.delete_ceph_user_home_dir")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "login_to_scripting_server_and_create_home_dir")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.update_ceph_quotas_config")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_ceph_quotas_attributes")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.get_ceph_quotas_config")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "create_dummy_files_for_ceph_user")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "log_results_of_current_iteration")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.datetime")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.get_end_time")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_perform_fs_quotas_operations__is_successful(self, mock_debug_log, mock_get_end_time, mock_datetime, *_):
        mock_get_end_time.return_value = datetime.now().replace(hour=12, minute=30, second=0, microsecond=0)
        mock_datetime.now.return_value = datetime.now().replace(hour=11, minute=30, second=0, microsecond=0)
        self.profile.perform_fs_quotas_operations()
        self.assertEqual(mock_debug_log.call_count, 28)

    @patch('enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.get_list_of_scripting_service_ips",
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.get_end_time",
           return_value=datetime.now().replace(hour=12, minute=30, second=0))
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.datetime",
           return_value=datetime.now().replace(hour=11, minute=30, second=0))
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.disable_ceph_quota_for_user")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.delete_ceph_user_home_dir")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "login_to_scripting_server_and_create_home_dir")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.update_ceph_quotas_config")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.check_ceph_quotas_attributes")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.get_ceph_quotas_config")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "create_dummy_files_for_ceph_user")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow."
           "log_results_of_current_iteration")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_perform_fs_quotas_operations__if_scripting_service_ips_not_found(self, mock_debug_log, mock_add_error, *_):
        self.profile.perform_fs_quotas_operations()
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.FsQuotas01Flow.execute_flow")
    def test_run_in_fs_quotas_01__is_successful(self, mock_execute_flow):
        fs_quotas_01.FS_QUOTAS_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    # fetch_cenm_deployment_values_id test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.parse_cenm_deployment_values_id_data")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.subprocess.check_output")
    def test_fetch_cenm_deployment_values_id__is_successful(self, mock_check_output,
                                                            mock_parse_cenm_deployment_values_id_data,
                                                            mock_debug_log):
        mock_check_output.return_value = ('[{"documents": [{"schema_name": "cENM_TAF_Properties", '
                                          '"document_id": "634e3c92cee5fdc8a0c8cafd", '
                                          '"schema_category": "other"},'
                                          '{"schema_name": "cenm_deployment_values",'
                                          '"document_id": "65143afbb0f7af6d86a4f840",'
                                          '"schema_category": "cenm"}]}]')
        fs_quotas_flow.fetch_cenm_deployment_values_id("cenm")
        self.assertEqual(mock_check_output.call_count, 1)
        self.assertEqual(mock_parse_cenm_deployment_values_id_data.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.parse_cenm_deployment_values_id_data")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.subprocess.check_output")
    def test_fetch_cenm_deployment_values_id__returns_none_if_curl_is_unsuccessful(self,
                                                                                   mock_check_output,
                                                                                   mock_parse_cenm_deployment_values_id_data,
                                                                                   mock_debug_log):
        mock_check_output.side_effect = [self.bad_command_result]
        fs_quotas_flow.fetch_cenm_deployment_values_id("cenm")
        self.assertEqual(mock_check_output.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)
        self.assertEqual(mock_parse_cenm_deployment_values_id_data.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.parse_cenm_deployment_values_id_data")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.subprocess.check_output")
    def test_fetch_cenm_deployment_values_id__if_response_is_empty(self, mock_check_output,
                                                                   mock_parse_cenm_deployment_values_id_data,
                                                                   mock_debug_log):
        mock_check_output.return_value = ''
        fs_quotas_flow.fetch_cenm_deployment_values_id("cenm")
        self.assertEqual(mock_check_output.call_count, 1)
        self.assertEqual(mock_parse_cenm_deployment_values_id_data.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 1)

    # verify_and_remove_ssh_keys test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    def test_verify_and_remove_ssh_keys__is_successful(self, mock_debug_log, mock_run_local_cmd, _):
        fs_quotas_flow.verify_and_remove_ssh_keys("1.1.1.1:50")
        self.assertEqual(mock_debug_log.call_count, 1)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    # fetch_cenm_deployment_type test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.json.loads")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.subprocess.check_output")
    def test_fetch_cenm_deployment_type__is_successful(self, mock_check_output, mock_logger, mock_json_loads):

        mock_json_loads.return_value = {"content": {"parameters": {"cenm_deployment_type": "CNIS"}}}
        mock_check_output.return_value = str(mock_json_loads.return_value)
        fs_quotas_flow.fetch_cenm_deployment_type("65143afbb0f7af6d86a4f840")
        self.assertEqual(mock_logger.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.subprocess.check_output")
    def test_fetch_cenm_deployment_type__if_unsuccessful(self, mock_check_output, mock_logger):
        mock_check_output.side_effect = [self.bad_command_result, "", ",",
                                         '{"parameters": {"cenm_deployment_type": ""}}',
                                         '{"parameters": {}}', '{"content": {"parameters": {}}}',
                                         '{"content": {"parameters": {"cenm_deployment": ""}}}',
                                         '{"content": {"parameters": {"cenm_deployment_type": ""}}}']
        for _ in range(8):
            fs_quotas_flow.fetch_cenm_deployment_type("65143afbb0f7af6d86a4f840")
        self.assertEqual(mock_logger.call_count, 15)

    # parse_cenm_deployment_values_id_data test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.json.loads")
    def test_parse_cenm_deployment_values_id_data__is_successful(self, mock_json_loads, mock_debug_log):
        mock_json_loads.return_value = [{"documents": [{"schema_name": "cENM_TAF_Properties",
                                                        "document_id": "634e3c92cee5fdc8a0c8cafd",
                                                        "schema_category": "other"},
                                                       {"schema_name": "cenm_deployment_values",
                                                        "document_id": "65143afbb0f7af6d86a4f840",
                                                        "schema_category": "cenm"}]}]
        fs_quotas_flow.parse_cenm_deployment_values_id_data(
            str(mock_json_loads.return_value),
            "command")
        self.assertEqual(mock_debug_log.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.json.loads")
    def test_parse_cenm_deployment_values_id_data__if_unsuccessful(self, mock_json_loads, mock_debug_log):
        mock_json_loads.side_effect = [ValueError, [{}]]
        for _ in range(2):
            self.assertEqual("",
                             fs_quotas_flow.parse_cenm_deployment_values_id_data(str(mock_json_loads.return_value),
                                                                                 "command"))
        self.assertEqual(mock_debug_log.call_count, 1)

    # verify_whether_deployment_type_is_cnis test cases
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.fetch_cenm_deployment_type",
           return_value="CNIS")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.fetch_cenm_deployment_values_id",
           return_value="65143afbb0f7af6d86a4f840")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.get_hostname_in_cloud_native")
    def test_verify_whether_deployment_type_is_cnis__is_successful(self, mock_get_hostname_in_cloud_native,
                                                                   mock_debug_log, *_):
        mock_get_hostname_in_cloud_native.return_value = (u'ddpenm6', u'cnisenm116_enm116')
        self.profile.verify_whether_deployment_type_is_cnis()
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.fetch_cenm_deployment_type",
           return_value="")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.fetch_cenm_deployment_values_id",
           return_value="65143afbb0f7af6d86a4f840")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow.get_hostname_in_cloud_native")
    def test_verify_whether_deployment_type_is_cnis__if_non_cnis_deployment(self, mock_get_hostname_in_cloud_native,
                                                                            mock_debug_log, *_):
        mock_get_hostname_in_cloud_native.return_value = (u'ddpenm6', u'cnisenm116_enm116')
        self.assertRaises(EnvironError, self.profile.verify_whether_deployment_type_is_cnis)
        self.assertEqual(mock_debug_log.call_count, 0)

    def tearDown(self):
        unit_test_utils.tear_down()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
