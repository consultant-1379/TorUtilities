from testslib import unit_test_utils
import unittest2
from mock import Mock, patch
from enmutils.lib import executor


class ExecutorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.executor.Executor.execute_command')
    def test_execute__success(self, mock_execute_cmd):
        cmd_obj = Mock()
        cmd_obj.initialize_attributes.return_value = None
        cmd_obj.pre_execute.return_value = None
        cmd_obj.post_execute.side_effect = lambda: setattr(exc.cmd_obj, 'finished', True)
        cmd_obj.finished.side_effect = [False, True]
        exc = executor.Executor(cmd_obj)
        exc.execute()
        self.assertEqual(1, mock_execute_cmd.call_count)

    @patch('enmutils.lib.executor.Executor.__init__', return_value=None)
    def test_execute_command__raises_not_implemented_error(self, _):
        self.assertRaises(NotImplementedError, executor.Executor(Mock()).execute_command)

    @patch('enmutils.lib.executor.threading._Timer.start')
    def test_start_time__success(self, mock_start):
        cmd_obj = Mock()
        cmd_obj.current_timeout = 0
        exc = executor.Executor(cmd_obj)
        exc._start_timer(Mock(), Mock())
        self.assertEqual(1, mock_start.call_count)

    @patch('enmutils.lib.executor.Executor.__init__', return_value=None)
    def test_command_cleanup__kills_process(self, _):
        cmd_obj, process = Mock(), Mock()
        process.poll.return_value = None
        exc = executor.Executor(cmd_obj)
        exc.timer = None
        exc._command_cleanup(process)
        self.assertEqual(1, process.kill.call_count)

    @patch('enmutils.lib.executor.Executor.__init__', return_value=None)
    @patch('enmutils.lib.executor.exception.process_exception')
    @patch('enmutils.lib.executor.log.logger.error')
    def test_command_cleanup__kills_process_exception(self, mock_error, mock_exception, _):
        cmd_obj, process = Mock(), Mock()
        process.poll.side_effect = Exception('Error')
        exc = executor.Executor(cmd_obj)
        exc.timer = None
        exc._command_cleanup(process)
        self.assertEqual(0, process.kill.call_count)
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(1, mock_exception.call_count)

    @patch('enmutils.lib.executor.Executor.__init__', return_value=None)
    def test_command_cleanup__no_process(self, _):
        cmd_obj, timer = Mock(), Mock()
        timer.is_alive.return_value = True
        exc = executor.Executor(cmd_obj)
        exc.timer = timer
        exc._command_cleanup()
        self.assertEqual(1, timer.cancel.call_count)
        self.assertIsNone(exc.timer)


class RemoteExecutorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.executor.log.logger.debug')
    @patch('enmutils.lib.executor.RemoteExecutor._command_cleanup')
    @patch('enmutils.lib.executor.RemoteExecutor._start_timer')
    def test_execute_command__success(self, mock_start, mock_clean_up, _):
        cmd_obj, connection = Mock(), Mock()
        remote = executor.RemoteExecutor(cmd_obj, connection, **{'add_linux_timeout': True, 'get_pty': True})
        stdout, stderr = Mock(), Mock()
        stdout.read.return_value = stderr.read.return_value = ""
        connection.exec_command.return_value = [Mock(), stdout, stderr]
        connection.timed_out = False
        setattr(remote.cmd_obj, 'async', False)
        remote.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertIn("timeout", remote.cmd_obj.cmd)
        self.assertEqual(1, connection.close.call_count)

    @patch('enmutils.lib.executor.log.logger.debug')
    @patch('enmutils.lib.executor.RemoteExecutor._command_cleanup')
    @patch('enmutils.lib.executor.RemoteExecutor._start_timer')
    def test_execute_command__async(self, mock_start, mock_clean_up, _):
        cmd_obj, connection = Mock(), Mock()
        remote = executor.RemoteExecutor(cmd_obj, connection, **{'add_linux_timeout': False, 'get_pty': False})
        connection.exec_command.return_value = [Mock()] * 3
        connection.timed_out = True
        remote.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(1, connection.close.call_count)

    @patch('enmutils.lib.executor.log.logger.debug')
    @patch('enmutils.lib.executor.RemoteExecutor._command_cleanup')
    @patch('enmutils.lib.executor.RemoteExecutor._start_timer')
    def test_execute_command__timed_out(self, mock_start, mock_clean_up, _):
        cmd_obj, connection = Mock(), Mock()
        remote = executor.RemoteExecutor(cmd_obj, connection, **{'add_linux_timeout': False, 'get_pty': False})
        stdout, stderr = Mock(), Mock()
        stdout.read.return_value = stderr.read.return_value = ""
        connection.exec_command.return_value = [Mock(), stdout, stderr]
        connection.timed_out = True
        setattr(remote.cmd_obj, 'async', False)
        remote.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(1, connection.close.call_count)
        self.assertEqual(remote.cmd_obj.response._rc, executor.COMMAND_TIMEOUT_RC)

    @patch('enmutils.lib.executor.log.logger.debug')
    @patch('enmutils.lib.executor.RemoteExecutor._command_cleanup')
    @patch('enmutils.lib.executor.RemoteExecutor._start_timer')
    def test_execute_command__host_died(self, mock_start, mock_clean_up, _):
        cmd_obj, connection = Mock(), Mock()
        remote = executor.RemoteExecutor(cmd_obj, connection, **{'add_linux_timeout': False, 'get_pty': False})
        stdout, stderr = Mock(), Mock()
        stdout.read.return_value = stderr.read.return_value = ""
        stdout.close.side_effect = executor.ProxyCommandFailure("cmd", "Error")
        connection.exec_command.return_value = [Mock(), stdout, stderr]
        connection.timed_out = False
        setattr(remote.cmd_obj, 'async', False)
        remote.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(1, connection.close.call_count)
        self.assertEqual(remote.cmd_obj.response._rc, executor.COMMAND_CONNECTION_CLOSED_RC)

    @patch('enmutils.lib.executor.log.logger.debug')
    @patch('enmutils.lib.executor.exception.process_exception')
    @patch('enmutils.lib.executor.log.logger.error')
    @patch('enmutils.lib.executor.RemoteExecutor._command_cleanup')
    @patch('enmutils.lib.executor.RemoteExecutor._start_timer')
    def test_execute_command__logs_exception(self, mock_start, mock_clean_up, mock_error, mock_process, _):
        cmd_obj, connection = Mock(), Mock()
        remote = executor.RemoteExecutor(cmd_obj, connection, **{'add_linux_timeout': False, 'get_pty': False})
        stdout, stderr = Mock(), Mock()
        stdout.read.return_value = stderr.read.return_value = ""
        stdout.close.side_effect = Exception("error")
        connection.exec_command.return_value = [Mock(), stdout, stderr]
        connection.timed_out = False
        setattr(remote.cmd_obj, 'async', False)
        remote.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(1, connection.close.call_count)
        self.assertEqual(remote.cmd_obj.response._rc, executor.COMMAND_CONNECTION_CLOSED_RC)
        self.assertEqual(1, mock_error.call_count)
        self.assertEqual(1, mock_process.call_count)


class LocalExecutorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.executor.subprocess.PIPE')
    @patch('enmutils.lib.executor.subprocess.STDOUT')
    @patch('enmutils.lib.executor.sys.executable', return_value='')
    @patch('enmutils.lib.executor.os.path.join')
    @patch('enmutils.lib.executor.subprocess.Popen')
    @patch('enmutils.lib.executor.LocalExecutor._command_cleanup')
    @patch('enmutils.lib.executor.LocalExecutor._start_timer')
    def test_execute_command__virtual_env(self, mock_start, mock_clean_up, mock_process, *_):
        cmd_obj = Mock()
        cmd_obj.activate_virtualenv = True
        cmd_obj.cmd = "cmd"
        pid = "123"
        mock_process.return_value.pid = pid
        local = executor.LocalExecutor(cmd_obj)
        setattr(local.cmd_obj, 'async', False)
        local.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(pid, local.cmd_obj.response._pid)

    @patch('enmutils.lib.executor.subprocess.PIPE')
    @patch('enmutils.lib.executor.subprocess.STDOUT')
    @patch('enmutils.lib.executor.subprocess.Popen')
    @patch('enmutils.lib.executor.LocalExecutor._command_cleanup')
    @patch('enmutils.lib.executor.LocalExecutor._start_timer')
    def test_execute_command__async(self, mock_start, mock_clean_up, mock_process, *_):
        cmd_obj = Mock()
        cmd_obj.activate_virtualenv = False
        cmd_obj.cmd = "cmd"
        pid = "123"
        mock_process.return_value.pid = pid
        local = executor.LocalExecutor(cmd_obj)
        setattr(local.cmd_obj, 'async', True)
        local.execute_command()
        self.assertEqual(0, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(pid, local.cmd_obj.response._pid)

    @patch('enmutils.lib.executor.subprocess.PIPE')
    @patch('enmutils.lib.executor.subprocess.STDOUT')
    @patch('enmutils.lib.executor.log.logger.error')
    @patch('enmutils.lib.executor.exception.process_exception')
    @patch('enmutils.lib.executor.subprocess.Popen')
    @patch('enmutils.lib.executor.LocalExecutor._command_cleanup')
    @patch('enmutils.lib.executor.LocalExecutor._start_timer')
    def test_execute_command__exception(self, mock_start, mock_clean_up, mock_process, mock_exception, *_):
        cmd_obj = Mock()
        cmd_obj.activate_virtualenv = False
        cmd_obj.cmd = "cmd"
        mock_process.return_value.pid = None
        local = executor.LocalExecutor(cmd_obj)
        setattr(local.cmd_obj, 'async', False)
        mock_start.side_effect = Exception("err")
        local.execute_command()
        self.assertEqual(1, mock_start.call_count)
        self.assertEqual(1, mock_clean_up.call_count)
        self.assertEqual(local.cmd_obj.response._rc, executor.COMMAND_EXCEPTION_RC)
        self.assertEqual(None, local.cmd_obj.response._pid)
        self.assertEqual(1, mock_exception.call_count)


class ExecutorModuleFunctionsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_remote_timeout_killer__closes_timed_out_connection(self):
        connection = Mock()
        connection.get_transport.return_value = None
        executor.remote_timeout_killer(connection)
        self.assertEqual(1, connection.close.call_count)

    def test_remote_timeout_killer__calls_close_again_if_transport_still_open(self):
        connection = Mock()
        connection.get_transport.return_value = Mock()
        executor.remote_timeout_killer(connection)
        self.assertEqual(2, connection.close.call_count)

    def test_local_timeout_killer__success(self):
        process = Mock()
        process.poll.return_value = None
        executor.local_timeout_killer(process)
        self.assertEqual(1, process.kill.call_count)

    def test_local_timeout_killer__time_out(self):
        process = Mock()
        process.poll.return_value = Mock()
        executor.local_timeout_killer(process)
        self.assertEqual(0, process.kill.call_count)
        self.assertEqual(process.returncode, executor.COMMAND_TIMEOUT_RC)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
