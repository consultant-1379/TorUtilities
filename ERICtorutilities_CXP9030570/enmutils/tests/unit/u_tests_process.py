#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib import process
from testslib import unit_test_utils


class ProcessUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_is_pid_running__returns_true_with_D_in_response(self, mock_run_local_cmd):
        response = Mock(rc=1, stdout="D", elapsed_time=.12)
        mock_run_local_cmd.return_value = response
        self.assertTrue(process.is_pid_running("1234"))

    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_is_pid_running__returns_true_with_R_in_response(self, mock_run_local_cmd):
        response = Mock(rc=1, stdout="R", elapsed_time=.12)
        mock_run_local_cmd.return_value = response
        self.assertTrue(process.is_pid_running("1234"))

    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_is_pid_running__returns_true_with_S_in_response(self, mock_run_local_cmd):
        response = Mock(rc=1, stdout="S", elapsed_time=.12)
        mock_run_local_cmd.return_value = response
        self.assertTrue(process.is_pid_running("1234"))

    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_is_pid_running__returns_true_with_T_in_response(self, mock_run_local_cmd):
        response = Mock(rc=1, stdout="T", elapsed_time=.12)
        mock_run_local_cmd.return_value = response
        self.assertTrue(process.is_pid_running("1234"))

    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_is_pid_running__returns_false_with_invalid_response(self, mock_run_local_cmd):
        response = Mock(rc=1, stdout="A", elapsed_time=.12)
        mock_run_local_cmd.return_value = response
        self.assertFalse(process.is_pid_running("1234"))

    @patch("enmutils.lib.process.is_pid_running")
    @patch("os.getpgid")
    @patch("os.killpg")
    def test_kill_pid__returns_false_if_pid_is_running(self, mock_os_killpg, mock_os_getpid, mock_is_pid_running):
        mock_os_killpg.return_value = None
        mock_os_getpid.return_value = None
        mock_is_pid_running.return_value = True
        self.assertFalse(process.kill_pid("999"))

    @patch('enmutils.lib.process.shell.run_local_cmd')
    @patch("os.getpgid")
    @patch("os.killpg")
    def test_kill_pid__returns_true_if_pid_is_not_running(self, mock_os_killpg, mock_os_getpid, mock_run_local_cmd):
        mock_os_killpg.return_value = None
        mock_os_getpid.return_value = None
        response = Mock(rc=1, stdout="A", elapsed_time=.12)
        mock_run_local_cmd.return_value = response
        self.assertTrue(process.kill_pid("1199"))

    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_get_current_rss_memory_for_current_process__is_successful(self, mock_run_local_cmd):
        mock_run_local_cmd.return_value = Mock(stdout="VmRSS:	   12345 kB\n")
        self.assertEqual(12345, process.get_current_rss_memory_for_current_process())

    @patch('enmutils.lib.process.shell.Command')
    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_get_current_rss_memory_for_current_process__return_zero_if_cannot_execute_command(
            self, mock_run_local_cmd, _):
        mock_run_local_cmd.return_value = Mock(ok=0)
        self.assertEqual(0, process.get_current_rss_memory_for_current_process())

    @patch('enmutils.lib.process.shell.Command')
    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_get_current_rss_memory_for_current_process__return_zero_if_output_unexpected(
            self, mock_run_local_cmd, _):
        mock_run_local_cmd.return_value = Mock(stdout="VmRSS:	   Some message\n")
        self.assertEqual(0, process.get_current_rss_memory_for_current_process())

    @patch('enmutils.lib.process.get_profile_daemon_pid', return_value=["1234", "1235", "1236"])
    @patch("enmutils.lib.process.kill_process_id")
    def test_kill_spawned_process__calls_kill_process_id(self, mock_kill, *_):
        process.kill_spawned_process("TEST_00", 1234)
        self.assertEqual(4, mock_kill.call_count)

    @patch('enmutils.lib.process.get_profile_daemon_pid', return_value=[])
    @patch("enmutils.lib.process.kill_process_id")
    def test_kill_spawned_process__doesnt_call_kill_process_id(self, mock_kill, *_):
        process.kill_spawned_process("TEST_00", 1234)
        self.assertEqual(0, mock_kill.call_count)

    @patch('os.path.isdir', return_value=True)
    @patch("os.kill")
    def test_kill_process_id__is_successful_if_pid_running(self, mock_kill, _):
        process.kill_process_id(9999, 15)
        mock_kill.assert_called_with(9999, 15)

    @patch('os.path.isdir', return_value=False)
    @patch("os.kill")
    def test_kill_process_id__is_successful_if_pid_not_running(self, mock_kill, _):
        process.kill_process_id(9999, 15)
        self.assertFalse(mock_kill.called)

    @patch('enmutils.lib.process.shell.Command')
    @patch('enmutils.lib.process.log.logger.debug')
    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_get_profile_daemon_pid__is_successful(self, mock_run_local_cmd, mock_log, _):
        mock_run_local_cmd.return_value = Mock(stdout=" \n1234\n1235\n1236\n ")
        self.assertEqual(["1234", "1235", "1236"], process.get_profile_daemon_pid("TEST_00"))
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils.lib.process.shell.Command')
    @patch('enmutils.lib.process.log.logger.debug')
    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_get_profile_daemon_pid__returns_empty_list_if_no_process_running(self, mock_run_local_cmd, mock_log, _):
        mock_run_local_cmd.return_value = Mock(stdout="\n")
        self.assertEqual([], process.get_profile_daemon_pid("TEST_00"))
        self.assertEqual(mock_log.call_count, 1)

    @patch('enmutils.lib.process.shell.Command')
    @patch('enmutils.lib.process.log.logger.debug')
    @patch('enmutils.lib.process.shell.run_local_cmd')
    def test_get_profile_daemon_pid__if_got_error(self, mock_run_local_cmd, mock_log, _):
        mock_run_local_cmd.return_value = Mock(stdout="error\n1234")
        self.assertEqual(['1234'], process.get_profile_daemon_pid("TEST_00"))
        self.assertEqual(mock_log.call_count, 1)

    @patch("commands.getstatusoutput", return_value=(0, "test_process_name"))
    def test_get_process_name__is_successful(self, _):
        self.assertEqual(process.get_process_name("12"), "test_process_name")

    @patch("commands.getstatusoutput", return_value=(1, "test_process_name"))
    def test_get_process_name__returns_unable_to_get_process_name_when_getstatusoutput_returns_nonzero_rc(self, _):
        self.assertEqual(process.get_process_name("12"), "unable_to_get_process_name")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
