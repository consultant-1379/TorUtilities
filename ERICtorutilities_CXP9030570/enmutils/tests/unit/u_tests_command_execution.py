#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib import command_execution as cme
from testslib import unit_test_utils


class CommandExecutionUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.host = 'host'
        self.user = 'user'

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.execute_cmd')
    def test_is_host_pingable__success(self, mock_execute, mock_debug):
        response = Mock(rc=0)
        mock_execute.return_value = response
        cme.is_host_pingable(self.host)
        mock_debug.assert_called_with("Verified that host {0} is pingable".format(self.host))

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.execute_cmd')
    def test_is_host_pingable__failure(self, mock_execute, mock_debug):
        response = Mock(rc=177)
        mock_execute.return_value = response
        cme.is_host_pingable(self.host)
        mock_debug.assert_called_with("Verified that host {0} is not pingable".format(self.host))

    @patch('enmutils.lib.command_execution.cache.get_enm_cloud_native_namespace', return_value='ns')
    @patch('enmutils.lib.command_execution.log.logger.debug')
    def test_convert_command_if_required__cloud_native(self, mock_debug, mock_namespace):
        cme.convert_command_if_required('ls', pod_name='pod', container_name='container')
        self.assertEqual(1, mock_namespace.call_count)
        mock_debug.assert_called_with("Command to be executed:: /usr/local/bin/kubectl --kubeconfig /root/.kube/config"
                                      " exec -n ns -c pod container -- bash -c 'ls' 2>/dev/null")

    @patch('enmutils.lib.command_execution.cache.get_enm_cloud_native_namespace')
    @patch('enmutils.lib.command_execution.log.logger.debug')
    def test_convert_command_if_required__success(self, mock_debug, mock_namespace):
        cme.convert_command_if_required('ls')
        self.assertEqual(0, mock_namespace.call_count)
        mock_debug.assert_called_with('Command to be executed:: ls')

    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=True)
    @patch('enmutils.lib.command_execution.cache.get_emp', return_value="EMP")
    def test_get_host_values__no_hostname_emp(self, mock_get_emp, _):
        cme.get_host_values()
        self.assertEqual(1, mock_get_emp.call_count)

    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=False)
    @patch('enmutils.lib.command_execution.cache.get_ms_host', return_value="MS")
    @patch('enmutils.lib.command_execution.cache.get_emp')
    def test_get_host_values__no_hostname_ms(self, mock_get_emp, mock_get_ms, *_):
        cme.get_host_values()
        self.assertEqual(0, mock_get_emp.call_count)
        self.assertEqual(1, mock_get_ms.call_count)

    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment')
    def test_get_host_values__hostname(self, mock_cloud):
        self.assertEqual((self.host, self.user), cme.get_host_values(hostname=self.host, username=self.user))
        self.assertEqual(0, mock_cloud.call_count)

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=True)
    def test_get_ssh_identity_file__selects_cloud_key(self, *_):
        self.assertEqual(cme.cache.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, cme.get_ssh_identity_file(**{}))

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=False)
    def test_get_ssh_identity_file__selects_physical_key(self, *_):
        self.assertEqual(cme.shell.DEFAULT_VM_SSH_KEYPATH, cme.get_ssh_identity_file(**{}))

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=False)
    def test_get_ssh_identity_file__uses_password(self, mock_cloud, _):
        self.assertEqual(None, cme.get_ssh_identity_file(**{'password': '1234'}))
        self.assertEqual(0, mock_cloud.call_count)

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=True)
    @patch('enmutils.lib.command_execution.cache.get_emp')
    def test_get_proxy_values__virtual_enm(self, mock_get_emp, *_):
        cme.get_proxy_values()
        self.assertEqual(1, mock_get_emp.call_count)

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.config.is_a_cloud_deployment', return_value=False)
    @patch('enmutils.lib.command_execution.cache.get_ms_host')
    def test_get_proxy_values__physical(self, mock_get_ms_host, *_):
        cme.get_proxy_values()
        self.assertEqual(1, mock_get_ms_host.call_count)

    @patch('enmutils.lib.command_execution.cache.get_ms_host', return_value='')
    @patch('enmutils.lib.command_execution.get_ssh_identity_file', return_value='file')
    @patch('enmutils.lib.command_execution.shell.get_connection_mgr')
    @patch('enmutils.lib.command_execution.get_proxy_values', return_value=('', ''))
    @patch('enmutils.lib.command_execution.shell.create_proxy')
    def test_get_connection_and_proxy__creates_proxy(self, mock_proxy, mock_values, mock_mgr, *_):
        connection = Mock()
        mock_mgr.return_value = connection
        cme.get_connection_and_proxy('host')
        self.assertEqual(1, mock_values.call_count)
        self.assertEqual(1, mock_proxy.call_count)
        self.assertEqual(1, connection.get_connection.call_count)
        mock_proxy.assert_called_with('host', '', '', ssh_identity_file=None)

    @patch('enmutils.lib.command_execution.get_ssh_identity_file', return_value='file')
    @patch('enmutils.lib.command_execution.shell.get_connection_mgr')
    @patch('enmutils.lib.command_execution.get_proxy_values', return_value=('', ''))
    @patch('enmutils.lib.command_execution.shell.create_proxy')
    def test_get_connection_and_proxy__no_proxy(self, mock_proxy, mock_values, mock_mgr, _):
        connection = Mock()
        mock_mgr.return_value = connection
        cme.get_connection_and_proxy('host', **{'user': 'user', 'password': 'pass'})
        self.assertEqual(0, mock_values.call_count)
        self.assertEqual(0, mock_proxy.call_count)
        self.assertEqual(1, connection.get_connection.call_count)

    @patch('enmutils.lib.command_execution.get_ssh_identity_file', return_value='file')
    @patch('enmutils.lib.command_execution.shell.get_connection_mgr', side_effect=Exception('Error'))
    def test_get_connection_and_proxy__raises_runtime_error(self, *_):
        self.assertRaises(RuntimeError, cme.get_connection_and_proxy, 'host', **{'user': 'user', 'password': 'pass'})

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.shell.close_proxy')
    def test_close_connection_and_proxy__no_proxy(self, mock_close, _):
        connection_manager = Mock()
        cme.close_connection_and_proxy(self.host, Mock(), connection_manager)
        self.assertEqual(0, mock_close.call_count)
        self.assertEqual(1, connection_manager.return_connection.call_count)

    @patch('enmutils.lib.command_execution.log.logger.debug')
    @patch('enmutils.lib.command_execution.shell.close_proxy')
    def test_close_connection_and_proxy__closes_proxy(self, mock_close, _):
        connection_manager = Mock()
        cme.close_connection_and_proxy(self.host, Mock(), connection_manager, proxy=Mock())
        self.assertEqual(1, mock_close.call_count)
        self.assertEqual(1, connection_manager.return_connection.call_count)

    @patch('enmutils.lib.command_execution.executor.RemoteExecutor.__init__', return_value=None)
    @patch('enmutils.lib.command_execution.close_connection_and_proxy')
    @patch('enmutils.lib.command_execution.executor.RemoteExecutor.execute')
    @patch('enmutils.lib.command_execution.get_connection_and_proxy', return_value=[Mock()] * 3)
    def test_execute_remote_cmd__success(self, mock_connection, mock_execute, mock_close, _):
        cme.execute_remote_cmd('ls', 'host')
        self.assertEqual(1, mock_connection.call_count)
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutils.lib.command_execution.executor.RemoteExecutor.__init__', return_value=None)
    @patch('enmutils.lib.command_execution.close_connection_and_proxy')
    @patch('enmutils.lib.command_execution.executor.RemoteExecutor.execute')
    @patch('enmutils.lib.command_execution.get_connection_and_proxy', return_value=[Mock()] * 3)
    def test_execute_remote_cmd__keep_connection_open(self, mock_connection, mock_execute, mock_close, _):
        cme.execute_remote_cmd('ls', 'host', **{'password': cme.NETSIM})
        mock_connection.assert_called_with('host', keep_connection_open=True, password='netsim', new_connection=False)
        self.assertEqual(1, mock_connection.call_count)
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutils.lib.command_execution.executor.RemoteExecutor.__init__', return_value=None)
    @patch('enmutils.lib.command_execution.executor.RemoteExecutor.execute', side_effect=Exception("Error"))
    @patch('enmutils.lib.command_execution.get_connection_and_proxy', return_value=[Mock()] * 3)
    @patch('enmutils.lib.command_execution.close_connection_and_proxy')
    def test_execute_remote_cmd__raises_runtime_error(self, mock_close, *_):
        self.assertRaises(RuntimeError, cme.execute_remote_cmd, 'ls', 'host')
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutils.lib.command_execution.cache.get_ms_host')
    @patch('enmutils.lib.command_execution.socket.gethostname')
    @patch('enmutils.lib.command_execution.convert_command_if_required')
    @patch('enmutils.lib.command_execution.executor.LocalExecutor.__init__', return_value=None)
    @patch('enmutils.lib.command_execution.executor.LocalExecutor.execute')
    @patch('enmutils.lib.command_execution.log.logger.debug')
    def test_execute_cmd__local_command(self, mock_debug, mock_execute, *_):
        cme.execute_cmd('cmd')
        mock_debug.assert_called_with('Executing local command.')
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.command_execution.cache.get_ms_host')
    @patch('enmutils.lib.command_execution.socket.gethostname', return_value='cloud-ms-1')
    @patch('enmutils.lib.command_execution.convert_command_if_required')
    @patch('enmutils.lib.command_execution.executor.LocalExecutor.__init__', return_value=None)
    @patch('enmutils.lib.command_execution.executor.LocalExecutor.execute')
    @patch('enmutils.lib.command_execution.log.logger.debug')
    def test_execute_cmd__local_command_v_app(self, mock_debug, mock_execute, *_):
        cme.execute_cmd('cmd', **{'remote_cmd': True})
        mock_debug.assert_called_with('Executing local command.')
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.command_execution.cache.get_ms_host', return_value='localhost')
    @patch('enmutils.lib.command_execution.socket.gethostname')
    @patch('enmutils.lib.command_execution.convert_command_if_required')
    @patch('enmutils.lib.command_execution.executor.LocalExecutor.__init__', return_value=None)
    @patch('enmutils.lib.command_execution.executor.LocalExecutor.execute')
    @patch('enmutils.lib.command_execution.log.logger.debug')
    def test_execute_cmd__local_command_lms(self, mock_debug, mock_execute, *_):
        cme.execute_cmd('ls', **{'remote_cmd': True})
        mock_debug.assert_called_with('Executing local command.')
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.command_execution.cache.get_ms_host')
    @patch('enmutils.lib.command_execution.socket.gethostname')
    @patch('enmutils.lib.command_execution.convert_command_if_required')
    @patch('enmutils.lib.command_execution.get_host_values', return_value=('', ''))
    @patch('enmutils.lib.command_execution.execute_remote_cmd')
    @patch('enmutils.lib.command_execution.log.logger.debug')
    def test_execute_cmd__remote_command(self, mock_debug, mock_execute, *_):
        cme.PROXY_HOSTS.append('remote_host')
        cme.execute_cmd('cmd', hostname='remote_host')
        mock_debug.assert_called_with('Executing remote command.')
        self.assertEqual(1, mock_execute.call_count)
        cme.PROXY_HOSTS = []

    @patch('enmutils.lib.command_execution.socket.gethostname')
    @patch('enmutils.lib.command_execution.convert_command_if_required')
    @patch('enmutils.lib.command_execution.get_host_values', return_value=('lms', ''))
    @patch('enmutils.lib.command_execution.is_host_pingable', return_value=False)
    @patch('enmutils.lib.command_execution.cache.get_ms_host', return_value='lms')
    @patch('enmutils.lib.command_execution.cache.get_emp', return_value='emp')
    @patch('enmutils.lib.command_execution.execute_remote_cmd')
    def test_execute_cmd__populate_and_proxy_host_not_pingable(self, mock_execute, mock_emp, mock_lms, *_):
        cme.PROXY_HOSTS = []
        response = cme.execute_cmd('cmd', hostname='lms')
        self.assertEqual(0, mock_execute.call_count)
        self.assertEqual(1, mock_emp.call_count)
        self.assertEqual(1, mock_lms.call_count)
        self.assertEqual(5, response.rc)
        cme.PROXY_HOSTS = []


if __name__ == "__main__":
    unittest2.main(verbosity=2)
