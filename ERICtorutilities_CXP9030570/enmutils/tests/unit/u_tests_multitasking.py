#!/usr/bin/env python
import time
from threading import ThreadError

import unittest2
from mock import Mock, patch, PropertyMock, mock_open, call

from enmutils.lib import (multitasking)
from enmutils.lib.multitasking import (UtilitiesWorkerEntry, AbstractUtilitiesDaemon, UtilitiesExternalDaemon,
                                       UtilitiesProcess, UtilitiesThread, _async_raise, should_workers_exit,
                                       get_num_tasks_running, add_profile_exception, create_pool_instance,
                                       invoke_instance_methods, join_tasks, log_debug)
from testslib import unit_test_utils


def good_func(interval):
    time.sleep(interval)


def bad_func():
    time.sleep(.001)


class MultitaskingUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.pidfile = '/var/tmp/enmutils/daemon/'

    def tearDown(self):
        unit_test_utils.tear_down()

    def _sleeper(self, interval):
        time.sleep(interval)

    def _exception_raiser(self):
        return 1 / 0

    def _custom_exception_raiser(self):
        raise RuntimeError("This is a test message")

    def test_thread_raises_exception(self):
        thread = multitasking.UtilitiesThread(None, self._exception_raiser, None)
        thread.start()
        time.sleep(.1)
        self.assertTrue(thread.has_raised_exception())

    def test_thread_exception_message_is_correct(self):
        thread = multitasking.UtilitiesThread(None, self._custom_exception_raiser, None)
        thread.start()
        time.sleep(.1)
        self.assertTrue(thread.has_raised_exception())
        self.assertEqual("This is a test message", thread.get_exception_msg())

    def test_waiting_for_threads_to_finish(self):
        thread1 = multitasking.UtilitiesThread(None, self._sleeper, None, [.2])
        thread2 = multitasking.UtilitiesThread(None, self._sleeper, None, [.4])
        thread_list = [thread1, thread2]
        thread1.start()
        thread2.start()
        multitasking.wait_for_tasks_to_finish(thread_list)
        self.assertFalse(thread1.is_alive())
        self.assertFalse(thread2.is_alive())

    def test_exception_raised_in_thread_is_raised_on_main_thread(self):
        thread = multitasking.UtilitiesThread(None, self._custom_exception_raiser, None)
        thread_list = [thread]
        self.assertFalse(thread.has_raised_exception())
        thread.start()
        self._sleeper(.1)
        multitasking.wait_for_tasks_to_finish(thread_list, timeout=1)
        self.assertTrue(thread.has_raised_exception())

    @patch('enmutils.lib.multitasking.cache.get', return_value=None)
    def test_should_workers_exit__sets_should_exit_to_false_when_cache_get_returns_none(self, _):
        self.assertFalse(should_workers_exit())

    @patch('enmutils.lib.multitasking.threading.enumerate')
    @patch('enmutils.lib.multitasking.threading.current_thread')
    @patch('enmutils.lib.multitasking.wait_for_tasks_to_finish')
    @patch('enmutils.lib.multitasking.cache.set')
    def test_terminate_threads__sets_should_workers_exit_to_false(self, mock_cache_set, *_):
        multitasking.terminate_threads()

        mock_cache_set.assert_called_with("should-workers-exit", False)

    @patch('enmutils.lib.multitasking.log_debug')
    @patch('enmutils.lib.multitasking.log.log_entry')
    @patch('enmutils.lib.multitasking.threading.Thread.is_alive')
    @patch('enmutils.lib.multitasking.threading.enumerate')
    @patch('enmutils.lib.multitasking.log.log_entry', return_value=None)
    @patch('enmutils.lib.multitasking.cache.set')
    @patch('enmutils.lib.multitasking.threading.current_thread')
    def test_terminate_threads__does_not_join_when_thread_is_not_live(self, mock_current_thread, *_):
        current_thread = mock_current_thread.return_value = Mock()
        some_other_thread = Mock()
        multitasking.initialized_utilities_threads = [some_other_thread, current_thread]

        multitasking.terminate_threads()

        self.assertTrue(some_other_thread.is_alive.called)
        self.assertTrue(current_thread.is_alive.called)

        self.assertTrue(some_other_thread.join.called)
        self.assertFalse(current_thread.join.called)

    @patch('enmutils.lib.multitasking.log_debug')
    @patch('enmutils.lib.multitasking.log.log_entry')
    @patch('enmutils.lib.multitasking.threading.current_thread')
    @patch('enmutils.lib.multitasking.threading.Thread.is_alive')
    @patch('enmutils.lib.multitasking.threading.enumerate')
    @patch("enmutils.lib.multitasking.log.logger.debug")
    @patch('enmutils.lib.multitasking.cache.set')
    @patch('enmutils.lib.multitasking.wait_for_tasks_to_finish')
    def test_terminate_threads__waits_for_tasks_to_finish(self, mock_wait_for_tasks_to_finish, *_):
        multitasking.terminate_threads(wait_for_threads_to_finish=True)

        self.assertEqual(1, mock_wait_for_tasks_to_finish.call_count)

    @patch('enmutils.lib.multitasking.log.log_entry')
    @patch('enmutils.lib.multitasking.threading.current_thread')
    @patch('enmutils.lib.multitasking.threading.Thread.is_alive')
    @patch('enmutils.lib.multitasking.threading.enumerate', return_value=[])
    @patch('enmutils.lib.multitasking.cache.set')
    @patch('enmutils.lib.multitasking.wait_for_tasks_to_finish')
    @patch('enmutils.lib.multitasking.log_debug')
    def test_terminate_threads__live_thread_counter_equals_zero_logs_join_sucessful(self, mock_debug, *_):
        multitasking.terminate_threads(wait_for_threads_to_finish=True)

        mock_debug.assert_called_with("All threads joined successfully on first attempt")

    @patch('enmutils.lib.multitasking.cache.set')
    @patch('enmutils.lib.multitasking.wait_for_tasks_to_finish')
    @patch('enmutils.lib.multitasking.log.log_entry', return_value=None)
    @patch('enmutils.lib.multitasking.threading.Thread.is_alive')
    @patch('enmutils.lib.multitasking.threading.enumerate')
    @patch('enmutils.lib.multitasking.log_debug')
    @patch('enmutils.lib.multitasking.threading.current_thread')
    def test_terminate_threads__increments_live_thread_counter_when_thread_found_in_enumerate(
            self, mock_current_thread, mock_debug, mock_enumerate, *_):
        current_thread = mock_current_thread.return_value = Mock()
        some_other_thread = Mock()
        mock_enumerate.return_value = [some_other_thread, current_thread]

        multitasking.terminate_threads()

        mock_debug.assert_called_with('Unable to join 1 threads...')

        self.assertTrue(some_other_thread.is_alive.called)
        self.assertTrue(current_thread.is_alive.called)

    def test_invoking_wait_for_threads_to_finish_with_no_registered_threads_does_nothing(self):
        multitasking.wait_for_tasks_to_finish([])

    def test_init__in_utilitiesworkerentry_initializes_and_returns_correct_values(self):
        mock_function = Mock()

        worker = UtilitiesWorkerEntry(mock_function, ['args1', 'args2'])

        self.assertEqual(mock_function, worker.function)
        self.assertListEqual(['args1', 'args2'], worker.arg_list)
        self.assertIsNone(worker.result)
        self.assertFalse(worker.finished)

    @patch('enmutils.lib.multitasking.os.path.isdir', return_value=False)
    @patch('enmutils.lib.multitasking.os.chmod')
    @patch('enmutils.lib.multitasking.filesystem.change_owner')
    @patch('enmutils.lib.multitasking.os.makedirs')
    def test_init__in_abstractutilitiesdaemon_makes_new_directory_if_piddir_not_found(self, mock_makedirs, mock_chown,
                                                                                      mock_chmod, mock_isdir):
        daemon = AbstractUtilitiesDaemon('id')
        daemon_path = "/var/tmp/enmutils/daemon"

        self.assertEqual(daemon.id, 'id')
        mock_makedirs.assert_called_with(daemon_path)
        mock_chown.assert_called_once_with(daemon_path, group_name="wheel")
        mock_chmod.assert_called_once_with(daemon_path, 0777)
        mock_isdir.assert_called_with(daemon_path)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch("enmutils.lib.multitasking.os.setpgrp")
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.write_pid_file')
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon._raise_if_running')
    @patch('enmutils.lib.multitasking.subprocess.Popen')
    @patch('enmutils.lib.multitasking.log')
    def test_start__in_abstractutilitiesdaemon_does_not_log_when_logger_is_none_and_execute_popen_with_correct_params(
            self, mock_log, mock_popen, mock_raise_if_running, mock_write_pid_file, mock_setpgrp, *_):
        daemon = multitasking.AbstractUtilitiesDaemon("some_id")
        daemon.cmd = "some_cmd"
        daemon.base_dir = "some_dir"
        daemon.close_all_fds = True
        mock_log.logger = None

        daemon.start()

        mock_popen.assert_called_with("some_cmd", stdout=-1, stderr=-2, cwd="some_dir", shell=False,
                                      close_fds=True, preexec_fn=mock_setpgrp)
        self.assertTrue(mock_raise_if_running.called)
        self.assertTrue(mock_write_pid_file.called)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=None)
    @patch("enmutils.lib.multitasking.log.logger.error")
    def test_stop__in_abstractutilitiesdaemon_logs_error_if_pid_not_found_in_pidfile(self, mock_error, *_):
        daemon = AbstractUtilitiesDaemon("some_id")
        daemon.pidfile = self.pidfile

        daemon.stop()

        mock_error.assert_called_with('PID file /var/tmp/enmutils/daemon/ does not exist; the daemon is not running...')

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=1234)
    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=True)
    @patch('enmutils.lib.multitasking.time.sleep')
    @patch('enmutils.lib.multitasking.signal')
    @patch('enmutils.lib.multitasking.process.kill_pid')
    def test_stop__in_abstractutilitiesdaemon_runs_16_times_if_daemon_not_killed(self, mock_kill_pid, mock_signal, *_):
        mock_signal.SIGKILL = 9
        mock_signal.SIGINT = 2
        mock_signal.SIGTERM = 15
        daemon = AbstractUtilitiesDaemon("some_id")
        daemon.pidfile = self.pidfile

        daemon.stop()

        self.assertEqual(mock_kill_pid.call_count, 16)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=1234)
    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=True)
    @patch('enmutils.lib.multitasking.time.sleep')
    @patch('enmutils.lib.multitasking.process.kill_pid', side_effect=IOError)
    @patch('enmutils.lib.multitasking.exception.process_exception')
    def test_stop__in_abstractutilitiesdaemon_kills_process_with_pid(self, mock_exception, *_):
        daemon = AbstractUtilitiesDaemon("some_id")
        daemon.name = 'daemon'
        daemon.pidfile = '/var/tmp/enmutils/daemon/'

        daemon.stop()

        self.assertEqual(1, mock_exception.call_count)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.start')
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.stop')
    def test_restart__in_abstractutilitiesdaemon_calls_start_and_stop_to_restart(self, mock_stop, mock_start, _):
        daemon = AbstractUtilitiesDaemon("some_id")
        daemon.restart()

        self.assertEqual(1, mock_stop.call_count)
        self.assertEqual(1, mock_start.call_count)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=None)
    def test_running__in_abstractutilitiesdaemon_returns_false_when_daemon_exists_and_running(self, *_):
        daemon = AbstractUtilitiesDaemon("some_id")

        self.assertFalse(daemon.running)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=True)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=1234)
    def test_running__in_abstractutilitiesdaemon_returns_true_when_daemon_exists_and_running(self, *_):
        daemon = AbstractUtilitiesDaemon("some_id")

        self.assertTrue(daemon.running)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    def test_init__in_utilitiesexternaldaemon_abbreviates_command(self, _):
        cmd = ('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. '
               'Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. '
               'Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. '
               'Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, '
               'imperdiet a, venenatis')

        cmd_list = list(cmd.split(" "))

        daemon = UtilitiesExternalDaemon('some_id', cmd_list)

        self.assertEqual('UtilitiesExternalDaemon-1 [Lorem]', daemon.desc)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    def test_init__in_utilitiesexternaldaemon_does_not_abbreviates_command(self, _):
        cmd_list = ["/bin/sh", "-c", "sleep", "100"]

        daemon = UtilitiesExternalDaemon('some_id', cmd_list)

        self.assertTrue(str(cmd_list) in daemon.desc)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    def test_init__in_utilitiesprocess_initializes_and_return_correct_default_values(self, _):
        process = UtilitiesProcess()

        self.assertFalse(process.daemon)
        self.assertIsNone(process.func_ref)
        self.assertIsNone(process.desc)
        self.assertIsNone(process.target)

    @patch('enmutils.lib.multitasking.multiprocessing.Process.start')
    @patch('enmutils.lib.multitasking.multiprocessing.Process.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesProcess.__init__', return_value=None)
    def test_start__in_utilitiesprocess_sets_desc_according_to_func_ref_name(self, *_):
        process = UtilitiesProcess()
        process.func_ref = Mock(__name__='function')
        process.name = 'UtilitiesProcess'
        process.start()

        self.assertTrue(('UtilitiesProcess-' and 'function()') in process.desc)

    @patch('enmutils.lib.multitasking.multiprocessing.Process.start')
    @patch('enmutils.lib.multitasking.multiprocessing.Process.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesProcess.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.log')
    def test_start__in_utilitiesprocess_sets_desc_according_to_target_name_and_calls_super_class_without_logging(
            self, mock_log, *_):
        process = UtilitiesProcess()
        process.func_ref = None
        process.name = 'UtilitiesProcess'
        process.target = Mock(__name__='target')
        mock_log.logger = None

        process.start()

        self.assertTrue(('UtilitiesProcess-' and 'target()') in process.desc)

    @patch('enmutils.lib.multitasking.multiprocessing.Process.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesProcess.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.multiprocessing.Process.run')
    def test_run__in_utilitiesprocess_runs_process_with_parent_class(self, mock_parent_run, *_):
        process = UtilitiesProcess()

        process.run()

        self.assertEqual(1, mock_parent_run.call_count)

    @patch('enmutils.lib.multitasking.UtilitiesProcess.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.exception.process_exception')
    @patch('enmutils.lib.multitasking.multiprocessing.Process.run')
    def test_run__in_utilitiesprocess_handles_exception_using_process_exception(self, mock_parent_run,
                                                                                mock_process_exception, _):
        mock_parent_run.side_effect = IOError
        process = UtilitiesProcess()
        process.desc = 'UtilitiesProcess'

        process.run()

        mock_process_exception.assert_called_with('Exception raised by process UtilitiesProcess')

    @patch('enmutils.lib.multitasking.UtilitiesProcess.__init__', return_value=None)
    def test_has_raised_exception__in_utilitiesprocess_returns_false_value(self, _):
        process = UtilitiesProcess()

        self.assertFalse(process.has_raised_exception())

    @patch('enmutils.lib.multitasking.UtilitiesThread.name', new_callable=PropertyMock)
    @patch('enmutils.lib.multitasking.UtilitiesThread.daemon', new_callable=PropertyMock)
    @patch('enmutils.lib.multitasking.threading.Thread.start')
    @patch('enmutils.lib.multitasking.threading.Thread.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.log')
    def test_start__in_utilitiesthread_sets_desc_according_to_func_ref_without_logging(self, mock_log, *_):
        thread = UtilitiesThread()
        thread.func_ref = Mock(__name__='function')
        mock_log.logger = None

        thread.start()

        self.assertTrue(('Thread-' and 'function()') in thread.desc)

    @patch('enmutils.lib.multitasking.UtilitiesThread.isAlive', return_value=False)
    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    def test_get_my_tid__in_utilitiesthread_raise_thread_error_if_not_alive(self, *_):
        thread = UtilitiesThread()

        self.assertRaises(ThreadError, thread._get_my_tid)

    @patch('enmutils.lib.multitasking.UtilitiesThread.isAlive', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    def test_get_my_tid__in_utilitiesthread_returns_thread_id_if_cached(self, *_):
        thread = UtilitiesThread()
        thread._thread_id = 1234

        self.assertEqual(1234, thread._get_my_tid())

    @patch('enmutils.lib.multitasking.UtilitiesThread.isAlive', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    def test_get_my_tid__in_utilitiesthread_raises_assertionerror(self, *_):
        thread = UtilitiesThread()
        thread._thread_id = None

        self.assertRaises(AssertionError, thread._get_my_tid)

    @patch('enmutils.lib.multitasking.UtilitiesThread.isAlive', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.threading._active')
    def test_get_my_tid__in_utilitiesthread_return_tid_if_in_threading_active_dict(self, mock_active, *_):
        thread = UtilitiesThread()
        mock_active.items.return_value = [(1234, thread)]
        thread._thread_id = None

        self.assertEqual(1234, thread._get_my_tid())

    @patch('enmutils.lib.multitasking.subprocess.Popen')
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.__init__', return_value=None)
    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.multitasking.process.is_pid_running', side_effect=[True, True, False])
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.get_pid', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.delete_pid_file')
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon._raise_if_running', return_value=None)
    @patch('enmutils.lib.multitasking.process.kill_pid')
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.write_pid_file')
    def test_starting_and_stopping_external_daemon_removes_process(self, mock_write_pid, mock_kill_pid, *_):
        daemon = multitasking.UtilitiesExternalDaemon("test-daemon", ["/bin/bash", "-c", "sleep", "100"])
        daemon.desc = 'some_desc'
        daemon.name = 'Daemon'
        daemon.cmd = ["/bin/bash", "-c", "sleep", "100"]
        daemon.close_all_fds = False
        daemon.base_dir = '/path/'
        daemon.pid = 'pid'
        daemon.start()
        self.assertTrue(mock_write_pid.called)
        daemon.stop()
        self.assertTrue(mock_kill_pid.called)

    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.__init__', return_value=None)
    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.multitasking.process.is_pid_running', side_effect=[True, False])
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.get_pid', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.delete_pid_file')
    def test_pid_file_is_removed_when_external_daemon_is_stopped(self, mock_delete_pid_file, *_):
        daemon = multitasking.UtilitiesExternalDaemon("test-daemon2", ["sleep", "100"])
        daemon.name = 'Daemon'
        daemon.pid = 'some_id'
        daemon.stop()

        self.assertTrue(mock_delete_pid_file.called)

    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=False)
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.get_pid', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.delete_pid_file')
    def test_everything_cleaned_up_if_external_daemon_killed_externally_before_stop(self, mock_delete_pid_file, *_):
        daemon = multitasking.UtilitiesExternalDaemon("test-daemon3", ["sleep", "100"])
        daemon.name = 'Daemon'
        daemon.pid = 'some_id'

        daemon.stop()

        self.assertTrue(mock_delete_pid_file.called)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    def test_creating_external_daemon_with_nonetype_cmd_raises_value_error(self, *_):
        self.assertRaises(ValueError, multitasking.UtilitiesExternalDaemon, "test-daemon4", None)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    def test_creating_external_daemon_with_empty_cmd_raises_value_error(self, *_):
        self.assertRaises(ValueError, multitasking.UtilitiesExternalDaemon, "test-daemon5", "")

    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesExternalDaemon._raise_if_running', side_effect=RuntimeError("Error"))
    def test_creating_the_same_external_daemon_twice_raises_runtime_error(self, *_):
        daemon2 = multitasking.UtilitiesExternalDaemon("test-daemon6", ["sleep", "100"])
        self.assertRaises(RuntimeError, daemon2.start)

    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.multitasking.process.is_pid_running', side_effect=[True, True, False])
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.get_pid', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.delete_pid_file')
    @patch('enmutils.lib.multitasking.UtilitiesDaemon._raise_if_running', return_value=None)
    @patch('subprocess.Popen')
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.write_pid_file')
    @patch('enmutils.lib.multitasking.process.kill_pid')
    def test_starting_and_stopping_daemon_removes_process(self, mock_kill_pid, mock_write_pid, *_):
        daemon = multitasking.UtilitiesDaemon("test-daemon7", good_func, [20])
        daemon.start()
        self.assertTrue(mock_write_pid.called)
        daemon.stop()
        self.assertTrue(mock_kill_pid.called)

    @patch('enmutils.lib.multitasking.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=False)
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.delete_pid_file')
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.get_pid', return_value=1234)
    @patch('enmutils.lib.multitasking.log.logger.info')
    def test_stop__for_utilitiesdaemon_pid_file_is_removed(self, mock_debug, mock_get_pid, mock_delete_pid, mock_running, _):
        daemon = multitasking.UtilitiesDaemon("test-daemon8", good_func, [20])
        daemon.name = 'test_daemon'
        daemon.pid = 1234

        daemon.stop()

        mock_get_pid.assert_called_once_with()
        mock_running.assert_called_once_with(1234)
        mock_delete_pid.assert_called_once_with()
        mock_debug.assert_called_with('Successfully terminated test_daemon [1234]')

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=False)
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.get_pid', return_value=True)
    @patch('enmutils.lib.multitasking.UtilitiesDaemon.delete_pid_file')
    def test_everything_cleaned_up_if_daemon_killed_externally_before_stop(self, mock_delete_pid_file, *_):
        daemon = multitasking.UtilitiesDaemon("test-daemon9", good_func, [20])
        daemon.name = 'daemon'
        daemon.pid = 123
        daemon.stop()
        self.assertTrue(mock_delete_pid_file.called)

    @patch("enmutils.lib.multitasking.persistence")
    @patch("enmutils.lib.multitasking.AbstractUtilitiesDaemon")
    @patch("enmutils.lib.multitasking.sys")
    @patch("enmutils.lib.multitasking.os")
    def test___init__for_utilitiesdaemon_is_successful_if_daemon_symlink_not_created(
            self, mock_os, *_):
        mock_os.path.dirname.return_value = "some_path1"
        test_profile_path = 'some_path1/daemons/TEST_PROFILE_01'
        mock_os.path.join.side_effect = ["some_path1/daemon",
                                         "some_path1/daemons",
                                         test_profile_path]
        mock_os.path.exists.return_value = False

        daemon = multitasking.UtilitiesDaemon("TEST_PROFILE_01", good_func, [20], log_identifier="test_profile_01")
        self.assertEqual(daemon.cmd, [test_profile_path, "TEST_PROFILE_01", "test_profile_01"])
        self.assertTrue(mock_os.mkdir.called)
        self.assertTrue(mock_os.symlink.called)

    @patch("enmutils.lib.multitasking.persistence")
    @patch("enmutils.lib.multitasking.AbstractUtilitiesDaemon")
    @patch("enmutils.lib.multitasking.sys")
    @patch("enmutils.lib.multitasking.os")
    def test___init__for_utilitiesdaemon_is_successful_if_daemon_symlink_already_created(
            self, mock_os, *_):
        mock_os.path.dirname.return_value = "some_path1"
        mock_os.path.join.side_effect = ["some_path1/daemon",
                                         "some_path1/daemons",
                                         "some_path1/daemons/TEST_PROFILE_01"]
        mock_os.path.exists.return_value = True

        daemon = multitasking.UtilitiesDaemon("TEST_PROFILE_01", good_func, [20], scheduler=True)
        self.assertEqual(daemon.cmd, ["some_path1/daemons/TEST_PROFILE_01", "TEST_PROFILE_01", "--scheduler"])
        self.assertFalse(mock_os.mkdir.called)
        self.assertFalse(mock_os.symlink.called)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    def test_creating_daemon_with_nonetype_func_reference_raises_value_error(self, *_):
        self.assertRaises(ValueError, multitasking.UtilitiesDaemon, "test-daemon", None)

    def test_join_tasks__returns_empty_list_task_not_in_initialized_utilities_threads(self):
        task, task1 = Mock(), Mock()

        self.assertListEqual([], join_tasks([task, task1]))
        self.assertTrue(task.has_raised_exception.called)
        self.assertTrue(task1.has_raised_exception.called)
        self.assertFalse(task.is_alive.called)
        self.assertFalse(task1.is_alive.called)

    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.multitasking.log.log_entry')
    @patch('datetime.timedelta', return_value=1)
    @patch('enmutils.lib.multitasking.timestamp.get_current_time', side_effect=[0, 0, 2])
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.multitasking.join_tasks')
    def test_wait_for_tasks_to_finish(self, mock_join_tasks, mock_debug, *_):
        task, task1 = Mock(), Mock()
        mock_join_tasks.return_value = [task]
        multitasking.wait_for_tasks_to_finish(tasks_list=[task, task1])
        log_msg = ("Could not join task {0} [{1}] - actions/commands are still running within thread"
                   .format(task.name, task.desc))
        mock_debug.assert_called_with(log_msg)

    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=True)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=1234)
    def test_raise_if_running__raises_runtime_error_if_pid_and_process_running(self, *_):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST_PROFILE_01")
        daemon.pidfile = "file"
        self.assertRaises(RuntimeError, daemon._raise_if_running)

    @patch('enmutils.lib.multitasking.process.is_pid_running', return_value=False)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.get_pid', return_value=1234)
    def test_raise_if_running__does_not_raise_runtime_error_if_process_not_running(self, *_):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST_PROFILE_01")
        daemon._raise_if_running()

    @patch("enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__", return_value=None)
    @patch('__builtin__.open', read_data="9999\n", new_callable=mock_open)
    def test_get_pid__is_successful_if_pid_not_set_and_pidfile_is_found(self, mock_file, *_):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST_PROFILE_01")
        daemon.pid = None
        daemon.pidfile = "blah"
        self.assertEqual(9999, daemon.get_pid())
        self.assertTrue(mock_file.called)

    @patch("enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__", return_value=None)
    @patch('__builtin__.open', new_callable=mock_open)
    def test_write_pid_file__is_successful(self, mock_open_file, _):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST_PROFILE_01")
        daemon.pidfile = "some_file"
        daemon.proc = Mock()
        daemon.proc.pid = 9999
        daemon.write_pid_file()
        mock_open_file.assert_called_with("some_file", 'w+')
        mock_open_file.return_value.write.assert_called_with("9999\n")

    @patch("enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__", return_value=None)
    @patch('__builtin__.open', side_effect=IOError)
    def test_get_pid__is_successful_if_pidfile_is_not_found(self, mock_file, *_):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST_PROFILE_01")
        daemon.pid = None
        daemon.pidfile = "blah"
        self.assertEqual(None, daemon.get_pid())
        self.assertTrue(mock_file.called)

    @patch("enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__", return_value=None)
    @patch('__builtin__.open')
    def test_get_pid__is_successful_if_pid_set_and_pidfile_is_found(self, mock_file, *_):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST_PROFILE_01")
        daemon.pid = 9999
        daemon.pidfile = "blah"
        self.assertEqual(9999, daemon.get_pid())
        self.assertFalse(mock_file.called)

    @patch("enmutils.lib.multitasking.create_pool_instance")
    def test_create_single_process_and_execute_task__is_successful_if_result_being_returned(self, mock_pool):
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), fetch_result=True)
        mock_pool.return_value.apply_async.assert_called_with("TEST_PROFILE_01", args=("ABC",))
        mock_pool.return_value.apply_async.return_value.get.assert_called_with(timeout=30 * 60)

    @patch("enmutils.lib.multitasking.CustomProcess")
    def test_create_single_process_and_execute_task__is_successful_if_result_not_being_returned(self, mock_process, *_):
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), timeout=60 * 60)
        mock_process.assert_called_with(target="TEST_PROFILE_01", args=("ABC",))
        mock_process.return_value.join.assert_called_with(timeout=60 * 60)

    @patch("enmutils.lib.multitasking.add_profile_exception")
    @patch("enmutils.lib.multitasking.CustomProcess")
    def test_create_single_process_and_execute_task__adds_exception_to_profile(self, mock_process, mock_add):
        mock_process.return_value.start.side_effect = IOError
        profile = Mock()
        mock_process.return_value.ident = 1234
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), fetch_result=False,
                                                            profile=profile)
        mock_process.assert_called_with(target="TEST_PROFILE_01", args=("ABC",))
        self.assertEqual(1, mock_add.call_count)

    @patch("enmutils.lib.multitasking.add_profile_exception")
    @patch("enmutils.lib.multitasking.log.logger.debug")
    @patch("enmutils.lib.multitasking.create_pool_instance")
    def test_create_single_process_and_execute_task__calls_close_join_if_exception(self, mock_pool, mock_debug, _):
        mock_pool.return_value.apply_async.side_effect = IOError("some error")
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), fetch_result=True)
        mock_pool.return_value.apply_async.assert_called_with("TEST_PROFILE_01", args=("ABC",))
        self.assertEqual(1, mock_pool.return_value.join.call_count)
        self.assertTrue(
            call("Encountered exception: [<type 'exceptions.IOError'> - some error]") in mock_debug.mock_calls)

    @patch("enmutils.lib.multitasking.add_profile_exception")
    @patch("enmutils.lib.multitasking.create_pool_instance")
    def test_create_single_process_and_execute_task__adds_exception_to_profile_pool(self, mock_pool, mock_add):
        mock_pool.return_value.apply_async.side_effect = IOError
        profile = Mock()
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), profile=profile,
                                                            fetch_result=True)
        mock_pool.return_value.apply_async.assert_called_with("TEST_PROFILE_01", args=("ABC",))
        self.assertEqual(1, mock_pool.return_value.join.call_count)
        self.assertEqual(1, mock_add.call_count)

    @patch("enmutils.lib.multitasking.create_pool_instance", return_value=None)
    @patch("enmutils.lib.multitasking.add_profile_exception")
    @patch('enmutils.lib.multitasking.log.logger.debug')
    def test_create_single_process_and_execute_task__pool_object_returns_none(self, mock_log, mock_add, _):
        profile = Mock()
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), profile=profile,
                                                            fetch_result=True)
        self.assertEqual(1, mock_add.call_count)
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils.lib.multitasking.CustomProcess", return_value=None)
    @patch("enmutils.lib.multitasking.add_profile_exception")
    @patch('enmutils.lib.multitasking.log.logger.debug')
    def test_create_single_process_and_execute_task__custom_process_object_returns_none(self, mock_log, mock_add, _):
        profile = Mock()
        multitasking.create_single_process_and_execute_task("TEST_PROFILE_01", ("ABC",), profile=profile,
                                                            fetch_result=False)
        self.assertEqual(1, mock_add.call_count)
        self.assertEqual(2, mock_log.call_count)

    @patch("enmutils.lib.multitasking.CustomProcess.__init__", return_value=None)
    @patch('__builtin__.super')
    def test_start__in_customprocess_is_successful(self, *_):
        custom_process = multitasking.CustomProcess()
        custom_process.start()

    @patch('enmutils.lib.multitasking.CustomProcess.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.CustomProcess.ident', new_callable=PropertyMock, return_value=1234)
    @patch('enmutils.lib.multitasking.multiprocessing.Process.run')
    @patch('enmutils.lib.log.logger.debug')
    def test_custom_process_run__logs_ident(self, mock_debug, *_):
        custom_process = multitasking.CustomProcess()
        custom_process.run()
        mock_debug.assert_called_with("Exiting run function of child process with identifier\t[1234]")

    @patch('enmutils.lib.multitasking.CustomProcess.ident', new_callable=PropertyMock, return_value=1234)
    @patch('enmutils.lib.multitasking.CustomProcess.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.log.logger.debug')
    @patch('enmutils.lib.multitasking.time.sleep', return_value=None)
    @patch('enmutils.lib.multitasking.multiprocessing.Process.is_alive')
    def test_wait_for_process_to_exit__is_successful(self, mock_is_alive, mock_sleep, mock_debug, *_):
        custom_process = multitasking.CustomProcess()
        mock_is_alive.side_effect = [True] * 10 + [False] * 2
        custom_process.wait_for_process_to_exit()
        self.assertEqual(mock_sleep.call_count, 10)

    @patch('enmutils.lib.multitasking.CustomProcess.ident', new_callable=PropertyMock, return_value=1234)
    @patch('enmutils.lib.multitasking.CustomProcess.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.log.logger.debug')
    @patch('enmutils.lib.multitasking.time.sleep', return_value=None)
    @patch('enmutils.lib.multitasking.multiprocessing.Process.is_alive')
    def test_wait_for_process_to_exit__is_successful_if_waiting_more_than_one_min(
            self, mock_is_alive, mock_sleep, mock_debug, *_):
        custom_process = multitasking.CustomProcess()
        mock_is_alive.side_effect = [True] * 61 + [False]
        custom_process.wait_for_process_to_exit()
        self.assertEqual(mock_sleep.call_count, 61)
        self.assertEqual(mock_debug.call_count, 13)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.os.remove')
    def test_delete_pid_file__success(self, mock_remove, _):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST")
        setattr(daemon, 'pidfile', "pid")
        daemon.delete_pid_file()
        self.assertEqual(1, mock_remove.call_count)

    @patch('enmutils.lib.multitasking.AbstractUtilitiesDaemon.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.log.logger.debug')
    @patch('enmutils.lib.multitasking.os.remove', side_effect=OSError("Error"))
    def test_delete_pid_file__logs_os_error(self, mock_remove, mock_debug, _):
        daemon = multitasking.AbstractUtilitiesDaemon("TEST")
        setattr(daemon, 'pidfile', "pid")
        daemon.delete_pid_file()
        self.assertEqual(1, mock_remove.call_count)
        mock_debug.assert_called_with("Failed to remove file: Error")

    @patch('enmutils.lib.multitasking.UtilitiesThread._get_my_tid', return_value=1234)
    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    @patch('enmutils.lib.multitasking._async_raise')
    def test_raise_exc__in_utilitiesthread_raise_correct_type_of_exception(self, mock_async_raise, *_):
        thread = UtilitiesThread()
        mock_exception = Mock()

        thread.raise_exc(mock_exception)

        mock_async_raise.assert_called_once_with(1234, mock_exception)

    @patch('enmutils.lib.multitasking.UtilitiesThread.__init__', return_value=None)
    @patch('enmutils.lib.multitasking.UtilitiesThread.raise_exc')
    def test_terminate__in_utilitiesthread_terminates_thread_using_raise_exc(self, mock_raise_exc, _):
        thread = UtilitiesThread()

        thread.terminate()

        mock_raise_exc.assert_called_once_with(SystemExit)

    @patch('enmutils.lib.multitasking.inspect.isclass', return_value=False)
    def test_async_raise__raises_type_error_when_not_exception_type(self, _):
        with self.assertRaises(TypeError) as e:
            _async_raise(1234, Mock())
        self.assertEqual(e.exception.message, "Only types can be raised (not instances)")

    @patch('enmutils.lib.multitasking.inspect.isclass', return_value=True)
    def test_async_raise__raises_valueerror_when_thread_id_not_correct(self, _):
        self.assertRaises(ValueError, _async_raise, 1234, AssertionError)

    @patch('enmutils.lib.multitasking.inspect.isclass', return_value=True)
    @patch('enmutils.lib.multitasking.ctypes.py_object')
    @patch('enmutils.lib.multitasking.ctypes.c_long')
    @patch('enmutils.lib.multitasking.ctypes.pythonapi.PyThreadState_SetAsyncExc')
    @patch('enmutils.lib.multitasking.log.logger.debug')
    def test_async_raise__raises_systemerror_when_response_greater_than_1_for_pythreadstate_setasyncexc(
            self, mock_debug, mock_pythreadstate_setasyncexc, mock_c_long, mock_py_object, _):
        mock_pythreadstate_setasyncexc.return_value = 2

        self.assertRaises(SystemError, _async_raise, 1234, Mock())
        mock_pythreadstate_setasyncexc.assert_called_with(mock_c_long.return_value, 0)
        mock_debug.assert_called_with('Failure of SystemExit for thread: 1234')

    @patch('enmutils.lib.multitasking.inspect.isclass', return_value=True)
    @patch('enmutils.lib.multitasking.ctypes.py_object')
    @patch('enmutils.lib.multitasking.ctypes.c_long')
    @patch('enmutils.lib.multitasking.ctypes.pythonapi.PyThreadState_SetAsyncExc', return_value=1)
    @patch('enmutils.lib.multitasking.log.logger.debug')
    def test_async_raise__logs_succsesful_exit_of_thread(self, mock_debug, mock_pythreadstate_setasyncexc,
                                                         mock_c_long, mock_py_object, _):
        _async_raise(1234, Mock())

        mock_pythreadstate_setasyncexc.assert_called_with(mock_c_long.return_value, mock_py_object.return_value)
        mock_debug.assert_called_once_with("Successfully initialised SystemExit of thread: 1234")

    @patch('enmutils.lib.multitasking.cache.get', return_value="yes exit")
    def test_should_workers_exit__returns_none_when_should_workers_exit_not_in_cache(self, mock_cache_get):
        self.assertEqual('yes exit', should_workers_exit())
        mock_cache_get.assert_called_once_with("should-workers-exit")

    def test_get_num_tasks_running__only_counts_alive_and_healthy_tasks(self):
        mock_task1 = Mock()
        mock_task2 = Mock()
        mock_task3 = Mock()
        mock_task1.is_alive.return_value = True
        mock_task2.is_alive.return_value = True
        mock_task3.is_alive.return_value = False
        mock_task1.has_raised_exception.return_value = False
        mock_task2.has_raised_exception.return_value = False
        mock_task3.has_raised_exception.return_value = False

        mock_task_list = [mock_task1, mock_task2, mock_task3]
        self.assertEqual(2, get_num_tasks_running(mock_task_list))

    def test_invoke_instance_methods__runs_methods_with_args_and_kwargs_on_target_instance_of_object(self):
        mock_instance = Mock()
        method_calls = [('method1', ['args1', 'args2'], {'task': 'test'})]

        self.assertIsNone(invoke_instance_methods(mock_instance, method_calls))

        mock_instance.method1.assert_called_with('args1', 'args2', task='test')

    @patch('enmutils.lib.multitasking.log.logger.debug')
    @patch('enmutils.lib.multitasking.log')
    def test_log_debug__does_not_log_statement_when_logger_is_none(self, mock_log, mock_debug):
        mock_log.logger = None

        log_debug('Check')

        self.assertFalse(mock_debug.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.multitasking.multiprocessing.Pool', side_effect=[OSError('Error'), Mock()])
    def test_create_pool_instance__retries_on_os_error(self, mock_pool, _):
        create_pool_instance("target")
        self.assertEqual(2, mock_pool.call_count)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.multitasking.multiprocessing.Pool',
           side_effect=[multitasking.multiprocessing.TimeoutError('Error'), multitasking.multiprocessing.TimeoutError('Error'),
                        multitasking.multiprocessing.TimeoutError('Error')])
    def test_create_pool_instance__retries_on_timeout_error_and_raises_environ_error(self, mock_pool, _):
        self.assertRaises(multitasking.exceptions.EnvironError, create_pool_instance, "target")
        self.assertEqual(3, mock_pool.call_count)

    def test_add_profile_exception__add_error_to_profile(self):
        profile = Mock()
        add_profile_exception("Exception", profile)
        self.assertEqual(1, profile.add_error_as_exception.call_count)

    @staticmethod
    def test_add_profile_exception__no_profile():
        # Added purely for coverage
        add_profile_exception("Exception")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
