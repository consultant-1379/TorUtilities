#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.ops import Ops
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class OpsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.node = [Mock()]
        self.user = Mock(username="test")
        self.scripting_ip = "102.21.12.1"
        self.is_enm_on_cn = True

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.ops.enm_deployment.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_values_from_global_properties')
    def test_init(self, mock_values_from_global_properties, *_):
        Ops().__init__(Mock())
        mock_values_from_global_properties.assert_called_with('ops=')

    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.ops.enm_deployment.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    def test_init__cn(self, mock_service_locations, mock_get_pod_hostnames, mock_get_cn_namespace, *_):
        Ops().__init__(Mock())
        mock_service_locations.assert_called_with('ops')
        mock_get_pod_hostnames.assert_called_with('general-scripting')
        self.assertTrue(mock_get_cn_namespace.called)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.log.logger.info")
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    def test_run_blade_runner_script_on_host__success(self, mock_run_cmd_on_emp_or_ms, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        response = Mock()
        response.rc = 0
        response.stdout = "please check logs at testfile"
        mock_run_cmd_on_emp_or_ms.return_value = response
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        Ops().run_blade_runner_script_on_host(user=user, node_name="xyz", host="abc", session_count=10)
        self.assertTrue(mock_run_cmd_on_emp_or_ms.called)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.log.logger.info")
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    def test_run_blade_runner_script_on_host__success_cn(self, mock_run_cmd_on_cn, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        response = Mock()
        response.rc = 0
        response.stdout = "please check logs at testfile"
        mock_run_cmd_on_cn.return_value = response
        setattr(Ops, 'scripting_ip', 142)
        Ops().run_blade_runner_script_on_host(user=user, node_name="xyz", host="abc", session_count=10)
        self.assertTrue(mock_run_cmd_on_cn.called)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_cmd_on_emp_or_ms", side_effect=EnvironError)
    def test_run_blade_runner_script_on_host__raises_environ_error(self, *_):
        ops = Ops()
        self.assertRaises(EnvironError, ops.run_blade_runner_script_on_host, "Test", "xyz", "abc", session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.ops.shell.run_cmd_on_cloud_native_pod", side_effect=EnvironError)
    def test_run_blade_runner_script_on_host__raises_environ_error__cn(self, *_):
        ops = Ops()
        self.assertRaises(EnvironError, ops.run_blade_runner_script_on_host, "Test", "xyz", "abc", session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    def test_run_blade_runner_script_on_host__raises_enm_application_error(self, mock_run_cmd_on_emp_or_ms, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        setattr(Ops, 'scripting_ip', 142)
        response = Mock()
        response.rc = 1
        response.stdout = "test"
        mock_run_cmd_on_emp_or_ms.return_value = response
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        ops = Ops()
        self.assertRaises(EnmApplicationError, ops.run_blade_runner_script_on_host, user, "xyz", "abc",
                          session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    def test_run_blade_runner_script_on_host__raises_enm_application_error__cn(self, mock_run_remote_cmd, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        setattr(Ops, 'scripting_ip', 142)
        response = Mock()
        response.rc = 1
        response.stdout = "test"
        mock_run_remote_cmd.return_value = response
        self.assertRaises(EnmApplicationError, Ops().run_blade_runner_script_on_host, user, "xyz", "abc",
                          session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch("enmutils_int.lib.ops.log.logger.debug")
    def test_check_sessions_count(self, mock_log, mock_run, *_):
        response = Mock()
        response.rc = 0
        mock_run.return_value = response
        setattr(Ops, 'scripting_ip', '122.12.12.1')
        Ops().check_sessions_count(Mock(username='test', password='king'), "abc", "xyz", session_count=10)
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_run.called)

    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=False)
    @patch('enmutils_int.lib.ops.enm_deployment.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    def test_run_blade_runner_script_on_vm(self, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        setattr(Ops, 'scripting_ip', 142)
        Ops().run_blade_runner_script_on_vm()

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.ops.get_internal_file_path_for_import", return_value="/home")
    @patch("enmutils_int.lib.ops.shell.copy_file_between_wlvm_and_cloud_native_pod")
    def test_copy_bladerunner_rest_script_to_scripting_host__success(self, mock_cmd, *_):
        setattr(Ops, 'scripting_pod_name', "pod1")
        response = Mock()
        response.rc = False
        mock_cmd.return_value = response
        Ops().copy_bladerunner_rest_script_to_scripting_host()

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch('enmutils_int.lib.ops.get_internal_file_path_for_import', return_value="/home")
    @patch('enmutils_int.lib.ops.shell.copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.ops.shell.copy_file_between_wlvm_and_cloud_native_pod')
    def test_copy_bladerunner_rest_script_to_scripting_host__copy_fail(self, mock_cmd, *_):
        setattr(Ops, 'scripting_pod_name', "pod1")
        response = Mock()
        response.rc = True
        mock_cmd.return_value = response
        Ops().copy_bladerunner_rest_script_to_scripting_host()

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch("enmutils_int.lib.ops.get_internal_file_path_for_import", return_value="/home")
    @patch("enmutils_int.lib.ops.shell.copy_file_between_wlvm_and_cloud_native_pod")
    @patch("enmutils_int.lib.ops.enm_deployment.get_enm_service_locations")
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.ops.shell.copy_file_between_wlvm_and_cloud_native_pod")
    def test_copy_bladerunner_rest_script_to_scripting_host__not_cn(self, *_):
        setattr(Ops, 'scripting_pod_name', "pod1")
        Ops().copy_bladerunner_rest_script_to_scripting_host()

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch("enmutils_int.lib.ops.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch("enmutils_int.lib.ops.log.logger.debug")
    def test_check_sessions_count__cn(self, mock_log, mock_run_cmd_on_cn, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        setattr(Ops, 'scripting_ip', 142)
        mock_run_cmd_on_cn.return_value = Mock(rc=0, stdout=30)
        Ops().check_sessions_count(user, "abc", "xyz", session_count=10)
        self.assertTrue(mock_log.called)
        self.assertTrue(mock_run_cmd_on_cn.called)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.ops.shell.run_cmd_on_emp_or_ms', side_effect=Exception)
    def test_check_sessions_count__raises_environ_error(self, *_):
        self.assertRaises(EnvironError, Ops().check_sessions_count, "Test", Mock(), "xyz", session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.ops.shell.run_cmd_on_cloud_native_pod', side_effect=Exception)
    def test_check_sessions_count__raises_environ_error_cn(self, *_):
        self.assertRaises(EnvironError, Ops().check_sessions_count, "Test", "abc", "xyz", session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    def test_check_sessions_count__raises_enm_application_error(self, mock_run, *_):
        mock_run.return_value = Mock(rc=1, stdout="test")
        setattr(Ops, 'scripting_ip', '122.12.12.1')
        self.assertRaises(EnmApplicationError, Ops().check_sessions_count, Mock(username='test', password='king'), "abc", "xyz", session_count=10)

    @patch('enmutils_int.lib.ops.Ops.__init__', return_value=None)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    def test_check_sessions_count__raises_enm_application_error_cn(self, mock_run_cmd_on_cn, *_):
        user = Mock()
        setattr(user, 'username', "user1")
        setattr(Ops, 'scripting_ip', 142)
        mock_run_cmd_on_cn.return_value = Mock(rc=1, stdout="test")
        self.assertRaises(EnmApplicationError, Ops().check_sessions_count, user, "abc", "xyz", session_count=10)

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.ops.get_ms_host", return_value=True)
    @patch("enmutils_int.lib.ops.is_host_ms", return_value=False)
    @patch('enmutils_int.lib.ops.log.logger.debug')
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.pexpect')
    def test_create_password_less_to_vm_penm__is_successful_with_prompt(self, mock_pexpect, mock_shell, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 0
        fail_response = Mock()
        fail_response.rc = 1
        success_response = Mock()
        success_response.rc = 0
        mock_shell.side_effect = [fail_response, success_response]
        mock_shell.return_value = fail_response
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        Ops().create_password_less_to_vm(self.user, generate_configurable_ip)
        mock_spawn.sendline.assert_any_call('yes')

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.ops.get_ms_host", return_value=True)
    @patch("enmutils_int.lib.ops.is_host_ms", return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.pexpect.spawn')
    def test_create_password_less_to_vm_penm__throws_exception(self, mock_spawn, mock_shell, *_):
        mock_spawn.return_value.expect.return_value = 2
        mock_resp = Mock()
        mock_resp.rc = 255
        mock_shell.return_value = mock_resp
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        ops = Ops()
        self.assertRaises(EnvironError, ops.create_password_less_to_vm, self.user, Mock())

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.ops.is_host_ms")
    @patch('enmutils_int.lib.ops.log.logger.debug')
    def test_create_password_less_to_vm_penm_is_ms_host__throws_exception(self, mock_is_ms_host, *_):
        mock_is_ms_host.return_value = True
        ops = Ops()
        self.assertRaises(RuntimeError, ops.create_password_less_to_vm, self.user, Mock())

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch("enmutils_int.lib.ops.is_host_ms", return_value=False)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.ops.log.logger.debug')
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.pexpect.spawn.__enter__')
    def test_create_password_less_to_vm_penm__is_successful_for_pwd_less_access_already_configured(self, mock_spawn,
                                                                                                   mock_shell, mock_log, *_):
        mock_resp = Mock()
        mock_resp.rc = 0
        mock_shell.return_value = mock_resp
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        Ops().create_password_less_to_vm(self.user, generate_configurable_ip())
        self.assertFalse(mock_spawn.called)
        mock_log.assert_called_with('Passwordless access is {0} for {1} user for {2} vm'.format
                                    ("already set", 'test', generate_configurable_ip()))

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch("enmutils_int.lib.ops.is_host_ms", return_value=False)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=False)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.log.logger.debug')
    @patch('enmutils_int.lib.ops.pexpect')
    def test_create_password_less_to_vm_penm__is_successful_for_no_pwd_prompt_with_ssh_copy(self, mock_pexpect,
                                                                                            mock_debug, mock_shell, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.side_effect = [0, 1, 0, 0, 1, 0]
        fail_response = Mock()
        fail_response.rc = 1
        success_response = Mock()
        success_response.rc = 0
        mock_shell.side_effect = [fail_response, success_response]
        mock_shell.return_value = success_response
        user = Mock(username='test', password='ksin')
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        Ops().create_password_less_to_vm(user, '121.12.12.1')
        mock_debug.assert_called_with('Passwordless access is {0} for {1} user for {2} vm'.format
                                      ("set", user.username, Ops.scripting_ip))

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.ops.log.logger.debug')
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.pexpect')
    def test_create_password_less_to_vm_cenm__is_successful_with_prompt(self, mock_pexpect, mock_shell, *_):
        mock_spawn = mock_pexpect.spawn().__enter__.return_value
        mock_spawn.expect.return_value = 0
        fail_response = Mock()
        fail_response.rc = 1
        success_response = Mock()
        success_response.rc = 0
        mock_shell.side_effect = [fail_response, success_response]
        mock_shell.return_value = fail_response
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        Ops().create_password_less_to_vm(self.user, generate_configurable_ip)
        mock_spawn.sendline.assert_any_call('yes')

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.pexpect.spawn')
    def test_create_password_less_to_vm_cenm__throws_exception(self, mock_spawn, mock_shell, *_):
        mock_spawn.return_value.expect.return_value = 2
        mock_resp = Mock()
        mock_resp.rc = 255
        mock_shell.return_value = mock_resp
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        ops = Ops()
        self.assertRaises(EnvironError, ops.create_password_less_to_vm, self.user, Mock())

    @patch('enmutils_int.lib.ops.enm_deployment.get_pod_hostnames_in_cloud_native')
    @patch('enmutils_int.lib.ops.get_enm_cloud_native_namespace')
    @patch('enmutils_int.lib.ops.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.ops.enm_deployment.get_enm_service_locations')
    @patch("enmutils_int.lib.ops.is_host_ms", return_value=False)
    @patch('enmutils_int.lib.ops.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.ops.log.logger.debug')
    @patch("enmutils_int.lib.ops.shell.run_remote_cmd")
    @patch('enmutils_int.lib.ops.pexpect.spawn.__enter__')
    def test_create_password_less_to_vm_cenm__is_successful_for_pwd_less_access_already_configured(self, mock_spawn,
                                                                                                   mock_shell, mock_log, *_):
        mock_resp = Mock()
        mock_resp.rc = 0
        mock_shell.return_value = mock_resp
        setattr(Ops, 'scripting_ip', '121.12.12.1')
        Ops().create_password_less_to_vm(self.user, generate_configurable_ip())
        self.assertFalse(mock_spawn.called)
        mock_log.assert_called_with('Passwordless access is {0} for {1} user for {2} vm'.format
                                    ("already set", 'test', generate_configurable_ip()))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
