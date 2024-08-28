#!/usr/bin/env python
import socket

import unittest2
from mock import Mock, patch

from enmutils.lib import cache, config
from enmutils.lib.exceptions import EnvironError
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class CacheUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.cache.get_haproxy_host')
    @patch('socket.getaddrinfo')
    def test_get_apache_ip_url__returns_random_cached_url(self, socket_patch, haproxy_patch):
        socket_patch.return_value = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '',
                                      ("some_ipv4_address", 443)),
                                     (10, 3, 0, '', ("some_ipv6_address", 443, 0, 0))]
        haproxy_patch.return_value = 'ieatenm5263-2.athtem.eei.ericsson.se'
        url = cache.get_apache_ip_url()
        self.assertTrue(url in ['https://some_ipv4_address:443', 'https://[some_ipv6_address]:443'])

    @patch('enmutils.lib.cache.get_haproxy_host')
    @patch('socket.getaddrinfo')
    def test_get_apache_ip_url__returns_ipv4_random_cached_url(self, socket_patch, haproxy_patch):
        socket_patch.return_value = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '',
                                      ("some_ipv4_address_1", 443)),
                                     (1, 1, 8, '', ("some_ipv4_address_2", 443, 0, 0))]
        haproxy_patch.return_value = 'ieatenm5263-2.athtem.eei.ericsson.se'
        url = cache.get_apache_ip_url()
        self.assertTrue(url in ['https://some_ipv4_address_2:443', 'https://some_ipv4_address_1:443'])

    @patch('enmutils.lib.cache.get_haproxy_host')
    @patch('socket.getaddrinfo')
    def test_get_apache_ip_url__returns_ipv6_random_cached_url(self, socket_patch, haproxy_patch):
        socket_patch.return_value = [(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_IP, '',
                                      ("some_ipv6_address", 443, 0, 0))]
        haproxy_patch.return_value = 'ieatenm5263-2.athtem.eei.ericsson.se'
        url = cache.get_apache_ip_url()
        self.assertTrue(url == 'https://[some_ipv6_address]:443')

    @patch('enmutils.lib.cache.get_haproxy_host')
    @patch('socket.getaddrinfo')
    @patch('enmutils.lib.cache.has_key')
    def test_get_apache_ip_url__returns_cached_url(self, mock_has_key, *_):
        mock_has_key.return_value = True
        with patch.dict("enmutils.lib.cache.__global_cache_dict", {"httpd-ip_url": "https://[some_ipv6_address]:443"}):
            self.assertEqual(cache.get_apache_ip_url(), "https://[some_ipv6_address]:443")

    @patch('enmutils.lib.shell.run_cmd_on_ms')
    def test_get_haproxy_host__returns_cached_hostname(self, run_cmd_on_ms_patch):
        res = Mock(rc=0, stdout='ieatenm5263-2.athtem.eei.ericsson.se')
        run_cmd_on_ms_patch.return_value = res
        self.assertEqual(cache.get_haproxy_host(), 'ieatenm5263-2.athtem.eei.ericsson.se')

    @patch('enmutils.lib.shell.run_cmd_on_ms')
    @patch('enmutils.lib.cache.get')
    def test_get_haproxy_host__raises_runtimeerror(self, mock_get, mock_run_cmd):
        response_mock = Mock()
        response_mock.rc = 1
        response_mock.stdout = ""
        mock_run_cmd.return_value = response_mock
        mock_get.return_value = None
        self.assertRaises(RuntimeError, cache.get_haproxy_host)

    @patch('enmutils.lib.cache.has_key')
    def test_get_haproxy_host__returns_cached_hostname_if_has_key_is_not_success(self, mock_has_key):
        mock_has_key.return_value = True
        with patch.dict("enmutils.lib.cache.__global_cache_dict", {"httpd-hostname": "ieatenm5263-2.athtem.eei.ericsson.se"}):
            self.assertEqual(cache.get_haproxy_host(), "ieatenm5263-2.athtem.eei.ericsson.se")

    @patch("enmutils.lib.cache.os")
    def test_get_haproxy_host__returns_cached_enm_url_key_has_success(self, mock_os):
        output = {'ENM_URL': "ieatenm5263-2.athtem.eei.ericsson.se"}
        mock_os.environ = output
        self.assertEqual(cache.get_haproxy_host(), "ieatenm5263-2.athtem.eei.ericsson.se")

    @patch('enmutils.lib.shell.run_cmd_on_ms')
    @patch("enmutils.lib.cache.is_emp")
    def test_get_haproxy_host_returns_cached_hostname_from_cloud(self, mock_is_emp, run_cmd_on_ms_patch):
        mock_is_emp.return_value = True
        res = Mock(rc=0, stdout='ieatenm5263-2.athtem.eei.ericsson.se')
        run_cmd_on_ms_patch.return_value = res
        self.assertEqual(cache.get_haproxy_host(), 'ieatenm5263-2.athtem.eei.ericsson.se')

    @patch('enmutils.lib.shell.run_cmd_on_ms')
    def test_is_enm_on_cloud(self, run_cmd_on_ms_patch):
        res = Mock(rc=0, stdout='ieatenm5263-2.athtem.eei.ericsson.se')
        run_cmd_on_ms_patch.return_value = res
        self.assertEqual(cache.is_enm_on_cloud(), False)

    def test_is_vnf_laf__returns_true_if_set(self):
        config.set_prop('VNF_LAF', generate_configurable_ip())
        self.assertTrue(cache.is_vnf_laf())

    @patch("enmutils.lib.config")
    @patch("enmutils.lib.cache.os")
    def test_get_vnf_laf__returns_cached_host_from_os_environ(self, mock_os, _):
        output = {'VNF_LAF': "test_host"}
        mock_os.environ = output
        self.assertEqual(cache.get_vnf_laf(), "test_host")

    @patch("enmutils.lib.config")
    def test_is_vnf_laf__returns_False_when_key_not_found(self, _):
        if config.has_prop('VNF_LAF'):
            config.set_prop('VNF_LAF', '')
        self.assertFalse(cache.is_vnf_laf())

    @patch("enmutils.lib.config")
    def test_is_emp_returns_true_if_set(self, _):
        config.set_prop('EMP', generate_configurable_ip())
        self.assertTrue(cache.is_emp())

    @patch("enmutils.lib.cache.os")
    def test_get_emp_returns_cached_host_from_os_environ(self, mock_os):
        output = {'EMP': "test_host"}
        mock_os.environ = output
        self.assertEqual(cache.get_emp(), "test_host")

    @patch("enmutils.lib.config")
    def test_is_emp_returns_False_when_key_not_found(self, _):
        if config.has_prop('EMP'):
            config.set_prop('EMP', '')
        self.assertFalse(cache.is_vnf_laf())

    @patch('enmutils.lib.shell.run_remote_cmd')
    def test_copy_cloud_user_ssh_private_key_file_to_emp__when_key_exists_already_success(self, run_remote_cmd_patch):
        response = Mock()
        response.rc = 0
        run_remote_cmd_patch.return_value = response
        self.assertTrue(cache.copy_cloud_user_ssh_private_key_file_to_emp())

    @patch('enmutils.lib.shell.run_local_cmd')
    @patch('enmutils.lib.shell.run_remote_cmd')
    @patch('enmutils.lib.log.logger.debug')
    def test_copy_cloud_user_ssh_private_key_file_to_emp__when_copy_from_workload_vm_success(self, mock_debug,
                                                                                             run_remote_cmd_patch,
                                                                                             run_local_cmd_patch):
        fail_response = Mock()
        fail_response.rc = 2
        success_response = Mock()
        success_response.rc = 0
        run_remote_cmd_patch.side_effect = [fail_response, success_response]
        run_local_cmd_patch.return_value = success_response
        self.assertTrue(cache.copy_cloud_user_ssh_private_key_file_to_emp())
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.shell.run_remote_cmd')
    @patch('enmutils.lib.shell.run_local_cmd')
    def test_copy_cloud_user_ssh_private_key_file_to_emp__when_copy_from_workload_vm_fails(self, run_local_cmd_patch,
                                                                                           run_remote_cmd_patch):
        response = Mock()
        response.rc = 2
        run_remote_cmd_patch.return_value = response
        run_local_cmd_patch.return_value = response
        self.assertRaises(EnvironError, cache.copy_cloud_user_ssh_private_key_file_to_emp)

    @patch('enmutils.lib.cache.shell.run_local_cmd')
    @patch('enmutils.lib.shell.run_remote_cmd')
    @patch('enmutils.lib.log.logger.debug')
    def test_copy_cloud_user_ssh_private_key_file_to_emp__when_move_fails(self, mock_debug,
                                                                          run_remote_cmd_patch,
                                                                          run_local_cmd_patch):
        fail_response = Mock()
        fail_response.rc = 2
        pass_response = Mock()
        pass_response.rc = 0
        run_remote_cmd_patch.side_effect = [fail_response, fail_response]
        run_local_cmd_patch.return_value = pass_response
        self.assertRaises(EnvironError, cache.copy_cloud_user_ssh_private_key_file_to_emp)
        self.assertTrue(mock_debug.called)

    @patch('enmutils.lib.cache.has_key', return_value=True)
    @patch('enmutils.lib.cache.get')
    def test_get_litp_admin_credentials__has_key_true_is_successful(self, mock_get, *_):
        mock_get.side_effect = ['test_user', 'test_password']
        self.assertEqual(cache.get_litp_admin_credentials(), ('test_user', 'test_password'))

    @patch('enmutils.lib.cache.has_key', return_value=False)
    @patch('enmutils.lib.cache.config.load_credentials_from_props')
    def test_get_litp_admin_credentials__sets_username_key_and_password_key(self, mock_load_credentials, _):
        test_credentials = ('test_user', 'test_password')
        mock_load_credentials.return_value = test_credentials
        self.assertEqual(cache.get_litp_admin_credentials(), test_credentials)
        mock_load_credentials.assert_called_with('litp_username', 'root_password')

    @patch('enmutils.lib.cache.has_key', return_value=False)
    @patch('enmutils.lib.cache.config.load_credentials_from_props')
    def test_get_litp_admin_credentials__sets_username_key_only(self, mock_load_credentials, _):
        test_credentials = ['test_user']
        mock_load_credentials.return_value = test_credentials
        self.assertEqual(cache.get_litp_admin_credentials(), test_credentials)
        mock_load_credentials.assert_called_with('litp_username', 'root_password')

    @patch('enmutils.lib.cache.has_key', return_value=False)
    @patch('enmutils.lib.cache.config.load_credentials_from_props')
    def test_get_litp_admin_credentials__raises_value_error(self, mock_load_credentials, _):
        test_credentials = ''
        mock_load_credentials.return_value = test_credentials
        self.assertRaises(ValueError, cache.get_litp_admin_credentials)

    @patch('enmutils.lib.cache._get_credentials')
    def test_get_workload_vm_credentials(self, mock_get_credentials):
        cache.get_workload_vm_credentials()
        self.assertEqual(1, mock_get_credentials.call_count)
        mock_get_credentials.assert_called_with('workload_vm_username', 'root_password')

    @patch("enmutils.lib.cache.get_enm_cloud_native_namespace", return_value="enm21")
    def test_is_enm_on_cloud_native__is_successful_if_cloud_native(self, _):
        self.assertTrue(cache.is_enm_on_cloud_native())

    @patch("enmutils.lib.cache.get_enm_cloud_native_namespace", return_value="")
    def test_is_enm_on_cloud_native__is_successful_if_not_cloud_native(self, _):
        self.assertFalse(cache.is_enm_on_cloud_native())

    @patch("enmutils.lib.cache.has_key", return_value=False)
    @patch("enmutils.lib.cache.get_haproxy_host", return_value="some_enm_url")
    @patch("enmutils.lib.shell.Command")
    @patch("enmutils.lib.shell.run_local_cmd")
    @patch("enmutils.lib.cache.set")
    def test_get_enm_cloud_native_namespace__returns_empty_string_if_not_cloud_native(
            self, mock_set, mock_run_local_cmd, *_):
        mock_run_local_cmd.return_value = Mock(rc=1, stdout="error")
        self.assertEqual("", cache.get_enm_cloud_native_namespace())
        self.assertFalse(mock_set.called)

    @patch("enmutils.lib.cache.has_key", return_value=False)
    @patch("enmutils.lib.cache.get_haproxy_host", return_value="some_enm_url")
    @patch("enmutils.lib.shell.Command")
    @patch("enmutils.lib.shell.run_local_cmd")
    @patch("enmutils.lib.cache.set")
    @patch("enmutils.lib.cache.get")
    def test_get_enm_cloud_native_namespace__returns_namespace_if_cloud_native_and_key_does_not_exist(
            self, mock_get, mock_set, mock_run_local_cmd, mock_command, *_):
        mock_run_local_cmd.return_value = Mock(rc=0, stdout="my_enm          uiserv                                "
                                                            "some_enm_url                     80, 443   5d1h\n")
        self.assertEqual("my_enm", cache.get_enm_cloud_native_namespace())
        mock_set.assert_called_with("enm_cloud_native_namespace", "my_enm")
        self.assertFalse(mock_get.called)
        mock_command.assert_called_with("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ingress "
                                        "--all-namespaces 2>/dev/null | egrep ui")

    @patch("enmutils.lib.cache.has_key", return_value=True)
    @patch("enmutils.lib.cache.get", return_value="my_enm")
    @patch("enmutils.lib.cache.set")
    def test_get_enm_cloud_native_namespace__returns_namespace_if_cloud_native_and_key_does_exist(
            self, mock_set, *_):
        self.assertEqual("my_enm", cache.get_enm_cloud_native_namespace())
        self.assertFalse(mock_set.called)

    @patch("enmutils.lib.cache.config")
    def test_is_host_physical_deployment(self, mock_config):
        mock_config.has_prop.return_value = True
        ip_addr = unit_test_utils.generate_configurable_ip()
        mock_config.get_prop.return_value = ip_addr
        self.assertTrue(cache.is_host_physical_deployment())

    @patch("enmutils.lib.cache.os")
    @patch("enmutils.lib.cache.config")
    def test_get_ms_host(self, mock_config, mock_os):
        ip_addr = unit_test_utils.generate_configurable_ip()
        mock_config.has_prop.return_value = False
        output = {'LMS_HOST': ip_addr}
        mock_os.environ = output
        cache.get_ms_host()
        self.assertEqual(ip_addr, output['LMS_HOST'])

    @patch('enmutils.lib.cache.filesystem.does_file_exist', return_value=False)
    @patch('enmutils.lib.cache.get_loader', return_value=True)
    @patch('enmutils.lib.cache.has_key', return_value=False)
    def test_verify_is_on_workload_vm_is_successful_and_returns_true(self, *_):
        self.assertEqual(cache.check_if_on_workload_vm(), True)

    @patch('enmutils.lib.cache.filesystem.does_file_exist', return_value=True)
    @patch('enmutils.lib.cache.get_loader', return_value=True)
    @patch('enmutils.lib.cache.has_key', return_value=False)
    def test_check_is_on_workload_vm_is_successful_and_returns_false_when_file_exists(self, *_):
        self.assertEqual(cache.check_if_on_workload_vm(), False)

    @patch('enmutils.lib.cache.has_key', return_value=True)
    @patch('enmutils.lib.cache.get')
    def test_verify_is_on_workload_vm__returns_value_when_key_exists(self, mock_get, _):
        mock_get.return_value = True

        self.assertEqual(cache.check_if_on_workload_vm(), True)

    @patch("time.time")
    @patch("enmutils.lib.mutexer.mutex")
    @patch("enmutils.lib.cache.copy_cloud_user_ssh_private_key_file_to_emp")
    @patch("enmutils.lib.cache.set")
    @patch("enmutils.lib.cache.has_key")
    def test_copy_cloud_user_ssh_private_key_to_enm__returns_true_if_key_has_not_been_copied_before(
            self, mock_has_key, mock_set, *_):
        mock_has_key.return_value = False
        cache.copy_cloud_user_ssh_private_key_to_enm()
        self.assertTrue(mock_set.called)

    @patch("enmutils.lib.mutexer.mutex")
    @patch("enmutils.lib.cache.set")
    @patch("enmutils.lib.cache.get")
    @patch("time.time")
    @patch("enmutils.lib.cache.has_key")
    def test_copy_cloud_user_ssh_private_key_to_enm__returns_true_if_key_was_copied_in_last_day(
            self, mock_has_key, mock_time, mock_get, mock_set, *_):
        mock_has_key.return_value = True
        time_now_sec = 1000
        mock_time.return_value = time_now_sec
        mock_get.return_value = 500
        cache.copy_cloud_user_ssh_private_key_to_enm()
        self.assertFalse(mock_set.called)

    @patch("enmutils.lib.mutexer.mutex")
    @patch("enmutils.lib.cache.copy_cloud_user_ssh_private_key_file_to_emp")
    @patch("enmutils.lib.cache.set")
    @patch("enmutils.lib.cache.get")
    @patch("time.time")
    @patch("enmutils.lib.cache.has_key")
    def test_copy_cloud_user_ssh_private_key_to_enm__returns_true_if_key_was_copied_over_1_day_ago(
            self, mock_has_key, mock_time, mock_get, mock_set, *_):
        mock_has_key.return_value = True
        time_now_sec = 1001 + 24 * 60 * 60
        mock_time.return_value = time_now_sec
        mock_get.return_value = 1000
        cache.copy_cloud_user_ssh_private_key_to_enm()
        self.assertTrue(mock_set.called)

    def test_has_key_and_remove__works_as_expected_for_given_dict_values(self):
        # When there is no 'user1' key
        self.assertEqual(cache.remove("user1"), None)
        # When 'user1' key is available
        with patch.dict("enmutils.lib.cache.__global_cache_dict", {"user1": "admin"}):
            self.assertTrue(cache.has_key("user1"))
            cache.remove("user1")
        # When 'user1' key is removed
        self.assertFalse(cache.has_key("user1"))

    @patch("enmutils.lib.cache.get_haproxy_host")
    def test_get_apache_url__returns_cached_apache_url(self, mock_haproxy_host):
        cache.get_apache_url()
        self.assertTrue(mock_haproxy_host.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
