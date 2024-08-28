#!/usr/bin/env python
import Queue
import collections

import paramiko
import unittest2
from mock import patch, Mock

from enmutils.lib import shell
from enmutils.lib.exceptions import EnvironError
from testslib import unit_test_utils


class ShellUnitTests(unittest2.TestCase):
    command_connection_closed_rc = 255

    def setUp(self):
        self.dummy_ip = "ip"
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.mutexer.mutex")
    @patch("enmutils.lib.log.logger.debug")
    def test_return_connection__logs_issue_with_used_remove(self, mock_debug, *_):
        host = "host"
        connection = Mock()
        connection.id = "1"
        connection.get_transport.return_value = False
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool[host] = {}
        conn_pool_mgr.remote_connection_pool[host]['available'] = Mock()
        conn_pool_mgr.remote_connection_pool[host]['used'] = []
        conn_pool_mgr.return_connection(host, connection)
        mock_debug.assert_called_with("The specified connection with id: 1 did not exist in the used connection queue.")

    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils.lib.mutexer.mutex")
    def test_return_connection__removes_from_used_if_connection_does_not_need_to_be_kept_open(self, *_):
        host = "host"
        connection = Mock()
        connection.get_transport.return_value = False
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool[host] = {}
        conn_pool_mgr.remote_connection_pool[host]['available'] = Mock()
        conn_pool_mgr.remote_connection_pool[host]['used'] = collections.deque([connection])

        conn_pool_mgr.return_connection(host, connection)
        self.assertEqual(0, len(conn_pool_mgr.remote_connection_pool[host]['used']))

    @patch('enmutils.lib.shell.mutexer.mutex')
    def test_return_connection__close_connection_if_open(self, _):
        connection = Mock()
        connection.get_transport.return_value = True
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool = []
        conn_pool_mgr.return_connection("host", connection)
        self.assertEqual(connection.close.call_count, 1)

    @patch('enmutils.lib.shell.mutexer.mutex')
    @patch('enmutils.lib.log.logger.debug')
    def test_return_connection__close_connection_if_open_logs_exception(self, mock_debug, _):
        connection = Mock()
        connection.get_transport.return_value = True
        connection.close.side_effect = Exception("Error")
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool = []
        conn_pool_mgr.return_connection("host", connection)
        self.assertEqual(connection.close.call_count, 1)
        mock_debug.assert_called_with("Failed to close connection, exception encountered: Error")

    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils.lib.mutexer.mutex")
    def test_return_connection__removes_an_invalid_connection_from_the_used_queue(self, *_):
        host = "host"
        connection1 = Mock()
        connection1.get_transport().is_authenticated.return_value = False
        connection2 = Mock()
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool[host] = {}
        conn_pool_mgr.remote_connection_pool[host]['available'] = Queue.Queue(shell.MAX_CONNECTIONS_PER_REMOTE_HOST)
        conn_pool_mgr.remote_connection_pool[host]['used'] = collections.deque([connection1, connection2])

        conn_pool_mgr.return_connection(host, connection1, keep_connection_open=True)
        self.assertEqual(1, len(conn_pool_mgr.remote_connection_pool[host]['used']))

    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils.lib.mutexer.mutex")
    def test_return_connection__removes_a_valid_connection_from_the_used_queue(self, *_):
        host = "host"
        connection1 = Mock()
        connection1.get_transport().is_authenticated.return_value = True
        connection2 = Mock()
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool[host] = {}
        available = conn_pool_mgr.remote_connection_pool[host]['available'] = Mock()
        available.put.side_effect = Queue.Full
        conn_pool_mgr.remote_connection_pool[host]['used'] = collections.deque([connection1, connection2])

        conn_pool_mgr.return_connection(host, connection1, keep_connection_open=True)
        self.assertEqual(1, len(conn_pool_mgr.remote_connection_pool[host]['used']))

    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils.lib.mutexer.mutex")
    def test_return_connection__removes_connection_from_used_queue_adds_to_available_when_the_connection_to_stay_open(
            self, *_):
        host = "host"
        connection1 = Mock()
        connection1.get_transport().is_authenticated.return_value = True
        connection2 = Mock()
        conn_pool_mgr = shell.ConnectionPoolManager()
        conn_pool_mgr.remote_connection_pool[host] = {}
        conn_pool_mgr.remote_connection_pool[host]['available'] = Queue.Queue(shell.MAX_CONNECTIONS_PER_REMOTE_HOST)
        conn_pool_mgr.remote_connection_pool[host]['used'] = collections.deque([connection1, connection2])

        conn_pool_mgr.return_connection(host, connection1, keep_connection_open=True)
        self.assertEqual(1, conn_pool_mgr.remote_connection_pool[host]['available'].qsize())
        self.assertEqual(1, len(conn_pool_mgr.remote_connection_pool[host]['used']))

    @patch("enmutils.lib.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.shell.Command._log_error_result")
    @patch("enmutils.lib.shell.Command._can_retry", return_value=True)
    @patch("enmutils.lib.shell.timestamp.get_elapsed_time", return_value=123)
    @patch("enmutils.lib.shell.timestamp.get_current_time", return_value="now")
    @patch("enmutils.lib.shell.Command._check_command_passed")
    @patch("enmutils.lib.shell.Command._sleep_between_attempts")
    def test_post_execute__sleep_between_attempts_is_called_if_connection_closed(
            self, mock_sleep_between_attempts, mock_check_command_passed, *_):
        command = shell.Command("dir")
        command.finished = False
        command.response = Mock(rc=self.command_connection_closed_rc)
        command.post_execute()
        self.assertTrue(mock_sleep_between_attempts.called)
        self.assertFalse(command.finished)
        self.assertFalse(mock_check_command_passed.called)

    @patch("enmutils.lib.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.shell.Command._can_retry", return_value=False)
    @patch("enmutils.lib.shell.timestamp.get_elapsed_time", return_value=123)
    @patch("enmutils.lib.shell.timestamp.get_current_time", return_value="now")
    @patch("enmutils.lib.shell.Command._check_command_passed")
    @patch("enmutils.lib.shell.Command._log_error_result")
    @patch("enmutils.lib.shell.Command._sleep_between_attempts")
    def test_post_execute__sleep_between_attempts_is_not_called_if_connection_closed_and_no_retry(
            self, mock_sleep_between_attempts, mock_log_error_result, mock_check_command_passed, *_):
        command = shell.Command("dir")
        command.finished = False
        command.response = Mock(rc=self.command_connection_closed_rc)
        command.post_execute()
        self.assertFalse(mock_sleep_between_attempts.called)
        self.assertTrue(mock_log_error_result.called)
        self.assertFalse(command.finished)
        self.assertFalse(mock_check_command_passed.called)

    @patch("enmutils.lib.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.shell.mutexer.mutex")
    @patch("enmutils.lib.log.logger.debug")
    def test_log_error_result__raise_environ_error(self, mock_log, *_):
        command = shell.Command("dir")
        command.finished = False
        command.cmd = Mock()
        command.response = Mock(rc=self.command_connection_closed_rc)
        command._log_error_result()
        self.assertEquals(
            "Encountered an error while carrying out the command : ERROR: Process terminated unexpectedly "
            "Please refer to logs", mock_log.call_args_list[0][0][0])

    @patch("enmutils.lib.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.shell.mutexer.mutex")
    @patch("enmutils.lib.log.logger.debug")
    def test_log_error_result__incorrect_command_rc(self, mock_log, *_):
        command = shell.Command("dir")
        command.finished = False
        command.cmd = Mock()
        command.response = Mock(rc=188)
        command._log_error_result()
        self.assertTrue(mock_log.called)

    @patch("enmutils.lib.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.shell.timestamp.get_elapsed_time", return_value=123)
    @patch("enmutils.lib.shell.timestamp.get_current_time", return_value="now")
    @patch("enmutils.lib.shell.Command._log_error_result")
    @patch("enmutils.lib.shell.Command._check_command_passed")
    @patch("enmutils.lib.shell.log.logger.debug")
    @patch("enmutils.lib.shell.Command._sleep_between_attempts")
    def test_post_execute__successful_when_cmd_is_being_logged(
            self, mock_log_error_result, mock_debug, mock_check_command_passed, *_):
        command = shell.Command("dir")
        command.finished = False
        command.log_cmd = True
        command.cmd = "dir"
        command.execution_host = "some_host"
        command.check_pass = True
        command.response = Mock(rc=0, elapsed_time=99, stdout="some_output")
        command.post_execute()
        self.assertEqual(0, mock_log_error_result.call_count)
        self.assertEqual(1, mock_check_command_passed.call_count)
        self.assertTrue(command.finished)
        mock_debug.assert_called_with("Executed command 'dir' on some_host [elapsed time 99s]\n  "
                                      "Command return code: 0\n  Command output: some_output")

    @patch("enmutils.lib.shell.Command.__init__", return_value=None)
    @patch("enmutils.lib.shell.timestamp.get_elapsed_time", return_value=123)
    @patch("enmutils.lib.shell.timestamp.get_current_time", return_value="now")
    @patch("enmutils.lib.shell.Command._log_error_result")
    @patch("enmutils.lib.shell.Command._check_command_passed")
    @patch("enmutils.lib.shell.log.logger.debug")
    @patch("enmutils.lib.shell.Command._sleep_between_attempts")
    def test_post_execute__successful_when_cmd_is_not_being_logged(
            self, mock_log_error_result, mock_debug, mock_check_command_passed, *_):
        command = shell.Command("dir")
        command.finished = False
        command.log_cmd = False
        command.cmd = "dir"
        command.execution_host = "some_host"
        command.check_pass = True
        command.response = Mock(rc=0, elapsed_time=99, stdout="some_output")
        command.post_execute()
        self.assertFalse(mock_log_error_result.called)
        self.assertTrue(mock_check_command_passed.called)
        self.assertTrue(command.finished)
        self.assertFalse(mock_debug.called)

    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection")
    def test_get_connection__request_for_connection_prompts_connection_creation_when_pool_is_empty(
            self, mock_connection_pool_manager):
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.get_connection("foo", "bar")
        self.assertTrue(mock_connection_pool_manager.called)

    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection")
    def test_get_connection__first_request_for_connection_for_host_creates_entries_in_connection_pool_dict(self, _):
        conn_mgr = shell.ConnectionPoolManager()
        self.assertFalse("foo" in conn_mgr.remote_connection_pool)
        conn_mgr.get_connection("foo", "bar")
        self.assertTrue("foo" in conn_mgr.remote_connection_pool)
        self.assertTrue("available" in conn_mgr.remote_connection_pool["foo"])
        self.assertTrue("used" in conn_mgr.remote_connection_pool["foo"])

    @patch("enmutils.lib.shell.ConnectionPoolManager.is_connected")
    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection")
    def test_get_connection__newly_created_connections_are_added_to_used_list(
            self, mock_establish_connection, mock_is_connected):
        fake_connection = object()
        mock_is_connected.return_value = True
        mock_establish_connection.return_value = fake_connection
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.get_connection("foo", "bar")

        # This will generate a ValueError if fake_connection is not in the used deque
        conn_mgr.remote_connection_pool["foo"]["used"].remove(fake_connection)

    @patch("enmutils.lib.shell.ConnectionPoolManager.is_connected")
    @patch("Queue.Queue.get")
    def test_get_connection__nonetype_connection_returned_if_queues_are_full_and_no_connections_available(
            self, mock_queue_get, mock_is_connected):
        mock_queue_get.side_effect = Queue.Empty()
        mock_is_connected.return_value = True
        host = "test-host"

        # Initialize the queues and fill up the used queue
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.remote_connection_pool[host] = {}
        conn_mgr.remote_connection_pool[host]['available'] = Queue.Queue(shell.MAX_CONNECTIONS_PER_REMOTE_HOST)
        conn_mgr.remote_connection_pool[host]['used'] = collections.deque(
            xrange(1, shell.MAX_CONNECTIONS_PER_REMOTE_HOST + 1))

        self.assertIsNone(conn_mgr.get_connection(host, "blah"))

    @patch("enmutils.lib.shell.ConnectionPoolManager.is_connected")
    def test_get_connection__connections_removed_from_available_queue_and_added_to_used_queue_when_requested(
            self, mock_is_connected):
        host = "test-host"
        connection1 = object()
        connection2 = object()
        mock_is_connected.return_value = True

        # Initialize the queues and add a couple of connections to the available queue
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.remote_connection_pool[host] = {}
        conn_mgr.remote_connection_pool[host]['available'] = Queue.Queue(shell.MAX_CONNECTIONS_PER_REMOTE_HOST)
        conn_mgr.remote_connection_pool[host]['available'].put(connection1)
        conn_mgr.remote_connection_pool[host]['available'].put(connection2)
        conn_mgr.remote_connection_pool[host]['used'] = collections.deque()

        self.assertEqual(connection1, conn_mgr.get_connection(host, "blah"))
        self.assertEqual(connection2, conn_mgr.get_connection(host, "blah"))
        self.assertEqual(0, conn_mgr.remote_connection_pool[host]['available'].qsize())

        # These removes will fail if the objects aren't in the used deque
        conn_mgr.remote_connection_pool[host]['used'].remove(connection1)
        conn_mgr.remote_connection_pool[host]['used'].remove(connection2)

    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection")
    @patch("enmutils.lib.shell.Queue.Queue.get")
    @patch("enmutils.lib.shell.Queue.Queue.qsize")
    @patch("enmutils.lib.shell.ConnectionPoolManager.is_connected")
    def test_get_connection__no_exception(self, mock_is_connected, mock_queue_qsize, mock_get, *_):
        mock_queue_qsize.return_value = 12
        mock_is_connected.return_value = False
        mock_get.return_value.user = "user"
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.get_connection("blah", "user")

    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection")
    @patch("enmutils.lib.shell.collections.deque")
    def test_get_connection__checked_connection(self, mock_collections, *_):
        conn_mgr = shell.ConnectionPoolManager()
        mock_collections.return_value = ["connection"]
        conn_mgr.get_connection("host", "user")

    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection", return_value=("host", "user"))
    def test_get_connection__to_establish_connection(self, _):
        conn_mgr = shell.ConnectionPoolManager()
        con = conn_mgr.get_connection("host-test", "user-test", new_connection=True)
        self.assertEqual(con, ("host", "user"))

    @patch("enmutils.lib.shell.log.logger.debug")
    def test_is_connected__raises_exception(self, mock_log):
        connection = Mock()
        conn_mgr = shell.ConnectionPoolManager()
        connection.get_transport.return_value.is_authenticated.side_effect = Exception
        conn_mgr.is_connected(connection)
        self.assertEqual(mock_log.call_count, 1)

    @patch("enmutils.lib.shell.log.logger.debug")
    @patch("enmutils.lib.shell.ConnectionPoolManager._establish_connection", return_value=None)
    def test_get_connection__connection_is_none(self, *_):
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.create_connection = True
        conn_mgr.get_connection("host-test", "user-test")

    @patch("enmutils.lib.shell.ConnectionPoolManager.is_connected")
    @patch("Queue.Queue.get")
    def test_get_connection__has_attribute_only(self, mock_queue_get, mock_is_connected):
        mock_queue_get.return_value = "user"
        mock_is_connected.return_value = True
        host = "test-host"
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.remote_connection_pool[host] = {}
        conn_mgr.remote_connection_pool[host]['available'] = Queue.Queue(shell.MAX_CONNECTIONS_PER_REMOTE_HOST)
        conn_mgr.remote_connection_pool[host]['used'] = collections.deque(range(1, 2))
        conn_mgr.get_connection(host, "blah")

    @patch("enmutils.lib.shell.ConnectionPoolManager.is_connected")
    @patch("Queue.Queue.get")
    def test_get_connection__has_attribute_and_user_value(self, mock_queue_get, mock_is_connected):
        mock_queue_get.side_effect = [Mock(user="user"), Mock(user="blah")]
        mock_is_connected.return_value = True
        host = "test-host"
        conn_mgr = shell.ConnectionPoolManager()
        conn_mgr.remote_connection_pool[host] = {}
        conn_mgr.remote_connection_pool[host]['available'] = Queue.Queue(shell.MAX_CONNECTIONS_PER_REMOTE_HOST)
        conn_mgr.remote_connection_pool[host]['used'] = collections.deque(xrange(1, 3))
        conn_mgr.get_connection(host, "blah")

    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=True)
    @patch("enmutils.lib.shell.paramiko.ProxyCommand")
    def test_create_proxy__is_successful(self, mock_proxycommand, *_):
        shell.create_proxy("remote_host", "username", "ms_host")
        mock_proxycommand.assert_called_with("ssh  -x -a -q -o StrictHostKeyChecking=no "
                                             "username@ms_host nc remote_host 22")

    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=False)
    @patch("enmutils.lib.shell.paramiko.ProxyCommand")
    def test_create_proxy__raises_runtimeerror_if_ssh_identity_file_is_not_found(self, mock_proxycommand, *_):
        with self.assertRaises(RuntimeError) as e:
            shell.create_proxy("remote_host", "username", "ms_host", "some_file")
        self.assertEqual("Cannot setup proxy as ssh_identity_file does not exist: some_file",
                         e.exception.message)
        self.assertFalse(mock_proxycommand.called)

    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=True)
    @patch("enmutils.lib.shell.paramiko.ProxyCommand", side_effect=Exception("some_error"))
    def test_create_proxy__raises_runtimeerror_if_proxycommand_returns_exception(self, mock_proxycommand, *_):
        with self.assertRaises(RuntimeError) as e:
            shell.create_proxy("remote_host", "username", "ms_host", "some_file")
        self.assertEqual("Unable to setup proxy on ms_host: some_error",
                         e.exception.message)
        mock_proxycommand.assert_called_with("ssh -i some_file -x -a -q -o StrictHostKeyChecking=no "
                                             "username@ms_host nc remote_host 22")

    def test_close_proxy__is_successful(self):
        proxy = Mock()
        shell.close_proxy(proxy)
        self.assertTrue(proxy.close.called)
        self.assertTrue(proxy.process.poll.called)

    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils.lib.mutexer.mutex")
    @patch("enmutils.lib.shell.ConnectionPoolManager._make_connection_with_host")
    def test_establish_connection__is_successful(self, mock_make_connection_with_host, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host, user, password = "some_host", "username", "some_password"
        ssh_identity_file = "some_file"
        allow_agent = look_for_keys = True
        ms_proxy = Mock()

        arg_list = [host, user, password]
        arg_dict = {"ssh_identity_file": ssh_identity_file, "ms_proxy": ms_proxy,
                    "allow_agent": allow_agent, "look_for_keys": look_for_keys}
        connection = Mock()
        mock_make_connection_with_host.return_value = connection

        connection_pool_manager.establish_connection(*arg_list, **arg_dict)
        mock_make_connection_with_host.assert_called_with(host, user, password,
                                                          ssh_identity_file=ssh_identity_file,
                                                          ms_proxy=ms_proxy, allow_agent=allow_agent,
                                                          look_for_keys=look_for_keys)

    @patch("paramiko.AutoAddPolicy")
    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=True)
    @patch("enmutils.lib.shell.ConnectionPoolManager.check_multiple_retry_needed")
    @patch("enmutils.lib.shell.config.get_encoded_password_and_decode")
    @patch("paramiko.SSHClient")
    def test_make_connection_with_host__is_successful(
            self, mock_sshclient, mock_password, mock_check_multiple_retry_needed, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host, user = "some_host", "username"
        password = mock_password.return_value = "some_password"
        ssh_identity_file = "path_to_some_file"
        allow_agent = look_for_keys = True
        ms_proxy = Mock()
        mock_connection = mock_sshclient.return_value

        connection_pool_manager._make_connection_with_host(host, user, password, ssh_identity_file=ssh_identity_file,
                                                           ms_proxy=ms_proxy, allow_agent=allow_agent,
                                                           look_for_keys=look_for_keys)

        mock_connection.connect.assert_called_with(
            host, username=user, password=password, key_filename=ssh_identity_file, timeout=7, sock=ms_proxy,
            allow_agent=allow_agent, look_for_keys=look_for_keys, auth_timeout=30)
        self.assertFalse(mock_check_multiple_retry_needed.called)

    @patch("paramiko.AutoAddPolicy")
    @patch("enmutils.lib.shell.config.get_encoded_password_and_decode", return_value="some_password")
    @patch("enmutils.lib.shell.ConnectionPoolManager.check_multiple_retry_needed")
    @patch("paramiko.SSHClient")
    def test_make_connection_with_host__is_successful_if_ssh_id_file_not_specified(
            self, mock_sshclient, mock_check_multiple_retry_needed, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        mock_connection = mock_sshclient.return_value

        connection_pool_manager._make_connection_with_host("some_host", "username", "some_password")

        mock_connection.connect.assert_called_with(
            "some_host", username="username", password="some_password", key_filename=None, timeout=7, sock=None,
            allow_agent=True, look_for_keys=True, auth_timeout=30)
        self.assertFalse(mock_check_multiple_retry_needed.called)

    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=False)
    @patch("enmutils.lib.shell.ConnectionPoolManager.check_multiple_retry_needed")
    @patch("enmutils.lib.shell.config.get_encoded_password_and_decode", return_value=None)
    @patch("paramiko.SSHClient")
    def test_make_connection_with_host__raises_environerror_if_ssh_id_file_does_not_exist(self, mock_sshclient, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        mock_connection = mock_sshclient.return_value

        self.assertRaises(EnvironError, connection_pool_manager._make_connection_with_host,
                          "some_host", "username", None, ssh_identity_file="some_file")

        self.assertFalse(mock_connection.connect.called)

    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=True)
    @patch("paramiko.AutoAddPolicy")
    @patch("enmutils.lib.shell.config.get_encoded_password_and_decode")
    @patch("enmutils.lib.shell.ConnectionPoolManager.check_multiple_retry_needed")
    @patch("paramiko.SSHClient")
    def test_make_connection_with_host__raises_sshexception(
            self, mock_sshclient, mock_check_multiple_retry_needed,
            mock_get_encoded_password_and_decode, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host, user = "some_host", "username"
        password = mock_get_encoded_password_and_decode.return_value = "some_password"
        ssh_identity_file = "path_to_some_file"
        allow_agent = look_for_keys = True
        mock_connection = mock_sshclient.return_value
        mock_connection.connect.side_effect = Exception
        mock_check_multiple_retry_needed.side_effect = Exception

        self.assertRaises(Exception, connection_pool_manager._make_connection_with_host,
                          host, user, password, ssh_identity_file=ssh_identity_file, ms_proxy=None,
                          allow_agent=allow_agent, look_for_keys=look_for_keys)

    @patch("enmutils.lib.shell.filesystem.does_file_exist", return_value=True)
    @patch("paramiko.AutoAddPolicy")
    @patch("enmutils.lib.shell.config.get_encoded_password_and_decode")
    @patch("enmutils.lib.shell.ConnectionPoolManager.check_multiple_retry_needed")
    @patch("paramiko.SSHClient")
    def test_make_connection_with_host__retries_connection_after_exception(
            self, mock_sshclient, mock_check_multiple_retry_needed,
            mock_get_encoded_password_and_decode, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        user = "username"
        password = mock_get_encoded_password_and_decode.return_value = "some_password"
        ssh_identity_file = "path_to_some_file"
        ms_proxy = allow_agent = look_for_keys = True
        mock_connection = mock_sshclient.return_value
        mock_connection.connect.side_effect = [Exception, Mock()]
        mock_check_multiple_retry_needed.return_value = True

        self.assertEqual(mock_connection,
                         connection_pool_manager._make_connection_with_host(host, user, password,
                                                                            ssh_identity_file=ssh_identity_file,
                                                                            ms_proxy=ms_proxy, allow_agent=allow_agent,
                                                                            look_for_keys=look_for_keys))

    @patch("time.sleep")
    @patch('enmutils.lib.shell.ConnectionPoolManager.__init__', return_value=None)
    @patch("enmutils.lib.shell.run_local_cmd")
    def test_check_multiple_retry_needed__is_successful_if_badhostkey_exception_encountered(
            self, mock_run_local_cmd, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        ms_proxy = True
        retry = 3

        error = paramiko.BadHostKeyException(host, Mock(), Mock())
        self.assertEqual(2, connection_pool_manager.check_multiple_retry_needed(error, host, ms_proxy, retry))
        self.assertTrue(mock_run_local_cmd.called)

    @patch("time.sleep")
    @patch('enmutils.lib.shell.ConnectionPoolManager.__init__', return_value=None)
    @patch("enmutils.lib.shell.run_local_cmd")
    def test_check_multiple_retry_needed__is_successful_if_authentication_exception_encountered_with_msproxy_set(
            self, mock_run_local_cmd, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        ms_proxy = True
        retry = 3

        error = paramiko.AuthenticationException()
        self.assertEqual(2, connection_pool_manager.check_multiple_retry_needed(error, host, ms_proxy, retry))
        self.assertTrue(mock_run_local_cmd.called)

    @patch("time.sleep")
    @patch('enmutils.lib.shell.ConnectionPoolManager.__init__', return_value=None)
    @patch("enmutils.lib.shell.run_local_cmd")
    def test_check_multiple_retry_needed__is_successful_if_authentication_exception_encountered_with_msproxy_unset(
            self, mock_run_local_cmd, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        ms_proxy = False
        retry = 3

        error = paramiko.AuthenticationException()
        self.assertEqual(2, connection_pool_manager.check_multiple_retry_needed(error, host, ms_proxy, retry))
        self.assertFalse(mock_run_local_cmd.called)

    @patch("time.sleep")
    @patch('enmutils.lib.shell.ConnectionPoolManager.__init__', return_value=None)
    def test_check_multiple_retry_needed__is_successful_if_protocol_banner_ssh_exception_encountered(self, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        ms_proxy = True
        retry = 3

        error = paramiko.SSHException("blah protocol banner blah")
        self.assertEqual(2, connection_pool_manager.check_multiple_retry_needed(error, host, ms_proxy, retry))

    @patch('time.sleep')
    @patch('enmutils.lib.shell.ConnectionPoolManager.__init__', return_value=None)
    def test_check_multiple_retry_needed__is_successful_if_no_existing_session_encountered(self, *_):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        ms_proxy = True
        retry = 3

        error = paramiko.SSHException("No existing session")
        self.assertEqual(2, connection_pool_manager.check_multiple_retry_needed(error, host, ms_proxy, retry))

    @patch("time.sleep")
    def test_check_multiple_retry_needed__raises_error_if_max_retries_exceeded(self, _):
        connection_pool_manager = shell.ConnectionPoolManager()
        host = "some_host"
        ms_proxy = True
        retry = 0

        error = paramiko.SSHException("blah")
        self.assertRaises(EnvironError,
                          connection_pool_manager.check_multiple_retry_needed, error, host, ms_proxy, retry)

    @patch("enmutils.lib.cache.get_enm_cloud_native_namespace", return_value="some_namespace")
    @patch("enmutils.lib.shell.run_local_cmd")
    @patch("enmutils.lib.shell.Command")
    def test_copy_remote_file_from_cloud_native_pod__is_successful_when_copying_from_pod(self, mock_command, *_):
        shell.copy_file_between_wlvm_and_cloud_native_pod("some_pod_name", "source_file", "dest_file", "from")
        command = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config cp some_namespace/some_pod_name:source_file"
                   " dest_file 2>/dev/null")
        mock_command.assert_called_with(command)

    @patch("enmutils.lib.cache.get_enm_cloud_native_namespace", return_value="some_namespace")
    @patch("enmutils.lib.shell.run_local_cmd")
    @patch("enmutils.lib.shell.Command")
    def test_copy_remote_file_from_cloud_native_pod__is_successful_when_copying_to_pod(self, mock_command, *_):
        shell.copy_file_between_wlvm_and_cloud_native_pod("some_pod_name", "source_file", "dest_file", "to")
        command = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config cp source_file "
                   "some_namespace/some_pod_name:dest_file 2>/dev/null")
        mock_command.assert_called_with(command)

    def test_get_connection_mgr__success(self):
        shell.connection_mgr = None
        connection_manager = shell.get_connection_mgr()
        self.assertIsInstance(connection_manager, shell.ConnectionPoolManager)

    def test_get_connection_mgr__singleton(self):
        conn = Mock()
        shell.connection_mgr = conn
        connection_manager = shell.get_connection_mgr()
        self.assertEqual(connection_manager, conn)


class ResponseUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.response = shell.Response(rc=0, stdout='{"stdout": "stdout"}', elapsed_time=1, command="cmd", pid="123")

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_response__properties(self):
        self.assertEqual(0, self.response.rc)
        self.assertEqual('{"stdout": "stdout"}', self.response.stdout)
        self.assertEqual(1, self.response.start_timestamp)
        self.assertEqual(None, self.response.end_timestamp)
        self.assertEqual(None, self.response.elapsed_time)
        self.assertEqual(True, self.response.ok)
        self.assertEqual("123", self.response.pid)

    def test_json__success(self):
        self.assertDictEqual({"stdout": "stdout"}, self.response.json())


class CommandUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_initialize_attributes__success(self):
        cmd = shell.Command("")
        cmd.initialize_attributes()
        self.assertEqual(1, cmd.retry_count)
        self.assertEqual(None, cmd.execution_host)
        self.assertEqual(2, cmd.retry_limit)
        self.assertEqual(60, cmd.timeout)

    def test_initialize_attributes__retry_limit(self):
        cmd = shell.Command("", allow_retries=False, retry_limit=3)
        cmd.initialize_attributes()
        self.assertEqual(1, cmd.retry_count)
        self.assertEqual(None, cmd.execution_host)
        self.assertEqual(3, cmd.retry_limit)
        self.assertEqual(60, cmd.timeout)

    def test_initialize_attributes__timeout(self):
        cmd = shell.Command("", allow_retries=False, timeout=600)
        cmd.initialize_attributes()
        self.assertEqual(1, cmd.retry_count)
        self.assertEqual(None, cmd.execution_host)
        self.assertEqual(1, cmd.retry_limit)
        self.assertEqual(600, cmd.timeout)

    @patch('enmutils.lib.shell.Response.__init__', return_value=None)
    def test_set_attributes__success(self, _):
        cmd = shell.Command("")
        cmd._set_attributes()
        self.assertIsNotNone(cmd.response)

    @patch('enmutils.lib.shell.timestamp.get_current_time', return_value=1)
    @patch('enmutils.lib.shell.Command._set_attributes')
    @patch('enmutils.lib.shell.Command._set_command_timeout')
    def test_pre_execute__success(self, mock_timeout, mock_attrs, _):
        response = Mock(_start_timestamp=2)
        cmd = shell.Command("", log_cmd=False)
        cmd.response = response
        cmd.pre_execute()
        self.assertEqual(1, mock_timeout.call_count)
        self.assertEqual(1, mock_attrs.call_count)

    @patch('enmutils.lib.shell.timestamp.get_current_time', return_value=1)
    @patch('enmutils.lib.shell.Command._set_attributes')
    @patch('enmutils.lib.shell.Command._set_command_timeout')
    @patch('enmutils.lib.shell.log.logger.debug')
    def test_pre_execute__logs_cmd(self, mock_debug, mock_timeout, mock_attrs, _):
        response = Mock(_start_timestamp=2)
        cmd = shell.Command("")
        cmd.response = response
        cmd.pre_execute()
        self.assertEqual(1, mock_timeout.call_count)
        self.assertEqual(1, mock_attrs.call_count)
        mock_debug.assert_called_with("Executing command on None: '' [timeout Nones]")

    @patch('enmutils.lib.shell.timestamp.get_current_time', return_value=1)
    @patch('enmutils.lib.shell.timestamp.get_elapsed_time', return_value=2)
    @patch('enmutils.lib.shell.Command._check_command_passed')
    def test_post_execute__success(self, mock_check, *_):
        response = Mock(rc=0)
        cmd = shell.Command("", check_pass=True)
        cmd.response = response
        cmd.post_execute()
        self.assertEqual(1, mock_check.call_count)

    @patch('enmutils.lib.shell.timestamp.get_current_time', return_value=1)
    @patch('enmutils.lib.shell.timestamp.get_elapsed_time', return_value=2)
    @patch('enmutils.lib.shell.Command._check_command_passed')
    @patch('enmutils.lib.shell.log.logger.debug')
    def test_post_execute__no_logging(self, mock_debug, mock_check, *_):
        response = Mock(rc=0)
        cmd = shell.Command("", log_cmd=False)
        cmd.response = response
        cmd.post_execute()
        self.assertEqual(0, mock_check.call_count)
        self.assertEqual(0, mock_debug.call_count)

    @patch('enmutils.lib.shell.timestamp.get_current_time', return_value=1)
    @patch('enmutils.lib.shell.timestamp.get_elapsed_time', return_value=2)
    @patch('enmutils.lib.shell.Command._check_command_passed')
    @patch('enmutils.lib.shell.Command._sleep_between_attempts')
    @patch('enmutils.lib.shell.Command._can_retry', return_value=True)
    @patch('enmutils.lib.shell.Command._log_error_result')
    def test_post_execute__retry_failure(self, mock_log_error, mock_retry, mock_sleep, *_):
        response = Mock(rc=177)
        cmd = shell.Command("")
        cmd.response = response
        cmd.post_execute()
        self.assertEqual(1, mock_log_error.call_count)
        self.assertEqual(1, mock_retry.call_count)
        self.assertEqual(1, mock_sleep.call_count)

    @patch('enmutils.lib.shell.timestamp.get_current_time', return_value=1)
    @patch('enmutils.lib.shell.timestamp.get_elapsed_time', return_value=2)
    @patch('enmutils.lib.shell.Command._check_command_passed')
    @patch('enmutils.lib.shell.Command._sleep_between_attempts')
    @patch('enmutils.lib.shell.Command._can_retry', return_value=False)
    @patch('enmutils.lib.shell.Command._log_error_result')
    def test_post_execute__no_retry_failure(self, mock_log_error, mock_retry, mock_sleep, *_):
        response = Mock(rc=211)
        cmd = shell.Command("")
        cmd.response = response
        cmd.post_execute()
        self.assertEqual(1, mock_log_error.call_count)
        self.assertEqual(1, mock_retry.call_count)
        self.assertEqual(0, mock_sleep.call_count)

    @patch('enmutils.lib.shell.log.logger.debug')
    def test_set_command_timeout__retry(self, mock_debug):
        cmd = shell.Command("")
        cmd.retry_count = 2
        cmd.current_timeout = 1
        cmd._set_command_timeout()
        self.assertEqual(1, mock_debug.call_count)

    @patch('enmutils.lib.shell.log.logger.debug')
    def test_set_command_timeout__no_retry(self, mock_debug):
        cmd = shell.Command("")
        cmd._set_command_timeout()
        self.assertEqual(0, mock_debug.call_count)

    @staticmethod
    def test_check_command_passed__success():
        response = Mock(rc=0)
        cmd = shell.Command("")
        cmd.response = response
        cmd._check_command_passed()

    def test_check_command_passed__raises_run_time_error(self):
        response = Mock(rc=1)
        cmd = shell.Command("")
        cmd.response = response
        self.assertRaises(RuntimeError, cmd._check_command_passed)

    @patch('enmutils.lib.shell.random.random', return_value=0.123)
    @patch('enmutils.lib.shell.log.logger.debug')
    @patch('enmutils.lib.shell.time.sleep')
    def test_sleep_between_attempts__success(self, mock_sleep, mock_debug, _):
        cmd = shell.Command("")
        cmd._sleep_between_attempts()
        mock_debug.assert_called_with("Sleeping for 0.49 seconds before re-attempting...")
        self.assertEqual(1, mock_sleep.call_count)

    def test_can_retry__no_retries(self):
        cmd = shell.Command("")
        cmd.allow_retries = None
        result = cmd._can_retry()
        self.assertEqual(False, result)
        self.assertEqual(True, cmd.finished)

    def test_can_retry__retry(self):
        cmd = shell.Command("")
        cmd.allow_retries = True
        cmd.retry_count = 1
        cmd.retry_limit = 2
        result = cmd._can_retry()
        self.assertEqual(True, result)
        self.assertEqual(False, cmd.finished)
        self.assertEqual(2, cmd.retry_count)

    @patch('enmutils.lib.shell.mutexer.mutex')
    @patch('enmutils.lib.shell.log.logger.debug')
    def test_log_error_result__timeout(self, mock_debug, _):
        response = Mock(rc=177)
        cmd = shell.Command("")
        cmd.response = response
        cmd._log_error_result()
        self.assertEqual(3, mock_debug.call_count)

    @patch('enmutils.lib.shell.mutexer.mutex')
    @patch('enmutils.lib.shell.log.logger.debug')
    def test_log_error_result__connection_closed(self, mock_debug, _):
        response = Mock(rc=255)
        cmd = shell.Command("")
        cmd.response = response
        cmd._log_error_result()
        self.assertEqual(2, mock_debug.call_count)


class RunCommandUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.cmd = "ls -l"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_local_cmd__success(self, mock_execute):
        shell.run_local_cmd(self.cmd)
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_remote_cmd__success(self, mock_execute):
        shell.run_remote_cmd(self.cmd, '', '')
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_remote_cmd_with_ms_proxy__success(self, mock_execute):
        shell.run_remote_cmd_with_ms_proxy(*self.cmd)
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_cmd_on_vm__success(self, mock_execute):
        shell.run_cmd_on_vm(self.cmd, '')
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_cmd_on_ms__success(self, mock_execute):
        shell.run_cmd_on_ms(self.cmd)
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.config.is_a_cloud_deployment', return_value=True)
    @patch('enmutils.lib.shell.run_cmd_on_vm')
    def test_run_cmd_on_emp_or_ms__is_success_on_cloud(self, mock_run_cmd_on_vm, _):
        shell.run_cmd_on_emp_or_ms(self.cmd)
        self.assertEqual(1, mock_run_cmd_on_vm.call_count)

    @patch('enmutils.lib.shell.config.is_a_cloud_deployment', return_value=False)
    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_cmd_on_emp_or_ms__is_success_on_physical(self, mock_execute, _):
        shell.run_cmd_on_emp_or_ms(self.cmd)
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.execute_command_wrapper')
    def test_run_cmd_on_cloud_native_pod__success(self, mock_execute):
        shell.run_cmd_on_cloud_native_pod(self.cmd, '', '')
        self.assertEqual(1, mock_execute.call_count)

    @patch('enmutils.lib.shell.command_execution.execute_cmd')
    def test_execute_command_wrapper__success(self, mock_execute):
        shell.execute_command_wrapper(self.cmd, {})
        self.assertEqual(1, mock_execute.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
