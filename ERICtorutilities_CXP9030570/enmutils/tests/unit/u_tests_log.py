#!/usr/bin/env python
import StringIO
import logging

import unittest2
from enmutils.lib import config, log
from mock import patch, Mock, call
from testslib import unit_test_utils


class LogUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        log.log_queue = Mock()
        log.manager = Mock()

    def tearDown(self):
        log.logger = Mock()
        unit_test_utils.tear_down()

    def test_check_use_color_returns_true_if_config_get_prop_equals_true(self):
        config.set_prop("print_color", "true")
        test_check_color = log._check_use_color()
        self.assertTrue(test_check_color)

    @patch("enmutils.lib.config.get_prop")
    def test_check_use_color_returns_false_if_config_get_prop_does_not_equal_true(self, _):
        config.set_prop("print_color", "false")
        test_check_color = log._check_use_color()
        self.assertFalse(test_check_color)

    def test_log_entry_changes_a_non_string_parameter_argument_to_a_string(self):
        a_list = ["some value"]
        try:
            log.log_entry(a_list)
        except TypeError:
            self.fail("List parameter was not converted to a string for use with the function")

    def test_simplified_log_stop(self):
        logger = logging.getLogger('test-logger')
        stream = StringIO.StringIO()
        handler = logging.StreamHandler(stream)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.info('test')
        logging.shutdown()
        logger.info('wildlife')
        self.assertTrue('wildlife' in stream.getvalue())
        log.logger = logger
        log.shutdown_handlers()
        logger.info('notlogged')
        self.assertFalse('notlogged' in stream.getvalue())

    @patch("enmutils.lib.log._prepare_log_dir")
    @patch("enmutils.lib.log.config.get_log_dir")
    @patch("os.path")
    def test_log_init__raises_error_when_no_log_dir_created(self, mock_os_path, *_):
        mock_os_path.isdir = Mock(return_value=False)
        self.assertRaises(RuntimeError, log.log_init)

        self.assertEqual(mock_os_path.isdir.call_count, 1)

    @patch("enmutils.lib.log.ProxyLogger")
    @patch("enmutils.lib.log.multiprocessing")
    @patch("enmutils.lib.log.atexit.register")
    @patch("enmutils.lib.log._prepare_log_dir")
    @patch("enmutils.lib.log.config.get_log_dir")
    @patch("enmutils.lib.log.os.path.isdir", return_value=True)
    @patch("enmutils.lib.log.multitasking.UtilitiesProcess")
    def test_log_init__is_successful(self, mock_utilities_process, *_):
        log.log_init()

        self.assertTrue(mock_utilities_process.return_value.start.called)

    @patch("os.makedirs")
    @patch("os.remove")
    @patch("os.path")
    def test__prepare_log_dir__log_path_is_removed_if_is_not_directory_and_new_log_dir_created(
            self, mock_os_path, mock_os_remove, mock_os_makedirs):
        mock_os_path.exists = Mock(return_value=True)
        mock_os_path.isdir = Mock(side_effect=[False, False, True])

        log._prepare_log_dir("some_path")

        self.assertEqual(mock_os_remove.call_count, 1)
        self.assertEqual(mock_os_makedirs.call_count, 1)
        self.assertEqual(mock_os_path.isdir.call_count, 2)

    @patch("os.makedirs")
    @patch("os.remove")
    @patch("os.path")
    def test_prepare_log_dir__creates_log_directory_when_no_path_exists(
            self, mock_os_path, mock_os_remove, mock_os_makedirs):
        mock_os_path.exists = Mock(return_value=False)
        mock_os_path.isdir = Mock(side_effect=[False, True])

        log._prepare_log_dir("some_path")

        self.assertEqual(mock_os_makedirs.call_count, 1)
        self.assertFalse(mock_os_remove.called)
        self.assertEqual(mock_os_path.isdir.call_count, 1)

    @patch('logging.shutdown')
    @patch('os.kill')
    @patch('time.sleep')
    def test_log_shutdown__is_successful_if_logqueue_is_empty(
            self, mock_sleep, mock_kill, mock_shutdown):
        log.log_shutdown()
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_kill.call_count, 1)
        self.assertEqual(mock_shutdown.call_count, 1)

    @patch('logging.shutdown')
    @patch('os.kill')
    @patch('time.sleep')
    def test_log_shutdown__will_wait_until_logqueue_is_empty(
            self, mock_sleep, *_):
        log.log_queue.empty.side_effect = [False, False, False, True]
        log.log_shutdown()
        self.assertEqual(mock_sleep.call_count, 4)

    @patch('logging.shutdown')
    @patch('os.kill')
    @patch('time.sleep')
    def test_log_shutdown__will_will_complete_anyway_if_exception_thrown_during_os_kill(
            self, mock_sleep, mock_kill, mock_shutdown):
        mock_kill.side_effect = Exception()
        log.logger = None
        log.log_shutdown()
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertFalse(mock_shutdown.called)

    @patch("logging.handlers.WatchedFileHandler")
    @patch("os.remove")
    @patch("os.path.exists", return_value=True)
    @patch("enmutils.lib.filesystem.create_dir")
    @patch("enmutils.lib.config.get_log_dir", return_value="enmutils/logs")
    def test_simplified_log_init__is_successful(self, *_):
        log.simplified_log_init("blah")
        log.simplified_log_init("blah", True)

    @patch("time.localtime")
    @patch("time.strftime", return_value="2018-11-15 19:18:16")
    @patch("threading.current_thread")
    def test_format__in_logformatter_is_successful_where_thread_is_set(self, mock_current_thread, *_):
        formatter = log.LogFormatter()
        mock_current_thread.return_value = Mock()
        mock_current_thread.return_value.name = "99999"
        record = Mock(created=1542309496, msecs=123, msg="Blah", levelname="DEBUG")
        final_msg = "2018-11-15 19:18:16,123 DEBUG   Blah (thread ID 99999)"
        self.assertEqual(final_msg, log.LogFormatter.format(formatter, record))

    @patch("time.localtime")
    @patch("time.strftime", return_value="2018-11-15 19:18:16")
    @patch("threading.current_thread", side_effect=Exception)
    def test_format__in_logformatter_is_successful_where_thread_is_not_set(self, *_):
        formatter = log.LogFormatter()
        record = Mock(created=1542309496, msecs=123, msg="Blah", levelname="DEBUG")
        final_msg = "2018-11-15 19:18:16,123 DEBUG   Blah"
        self.assertEqual(final_msg, log.LogFormatter.format(formatter, record))

    @patch("enmutils.lib.log.inspect.stack")
    def test_get_identifier__in_proxylogger_returns_caller(self, mock_stack, *_):
        proxy_logger = log.ProxyLogger()
        mock_stack.return_value = [Mock(), Mock(), [Mock(), Mock(), Mock(), "some_caller"]]
        self.assertEqual("some_caller", proxy_logger.get_caller())

    @patch("enmutils.lib.log.os.getpid", return_value=99999)
    @patch("enmutils.lib.log.multiprocessing")
    @patch("enmutils.lib.log.threading")
    def test_get_identifier__in_proxylogger_returns_id_of_thread(self, mock_threading, mock_multiprocessing, *_):
        proxy_logger = log.ProxyLogger()
        current_thread = Mock()
        current_thread.name = "ABC"
        mock_threading.current_thread.return_value = current_thread
        mock_multiprocessing.current_process.side_effect = Exception
        self.assertEqual("(thread ID ABC)", proxy_logger.get_identifier())

    @patch("enmutils.lib.log.os.getpid", return_value=99999)
    @patch("enmutils.lib.log.multiprocessing")
    @patch("enmutils.lib.log.threading")
    def test_get_identifier__in_proxylogger_returns_pid_if_mainthread(self, mock_threading, mock_multiprocessing, *_):
        proxy_logger = log.ProxyLogger()
        current_thread = Mock()
        current_thread.name = "MainThread0"
        mock_threading.current_thread.return_value = current_thread
        mock_multiprocessing.current_process.side_effect = Exception
        self.assertEqual("(PID 99999)", proxy_logger.get_identifier())

    @patch("enmutils.lib.log.os.getpid", return_value=99999)
    @patch("enmutils.lib.log.multiprocessing")
    @patch("enmutils.lib.log.threading")
    def test_get_identifier__in_proxylogger_returns_id_of_multiprocessing_process(
            self, mock_threading, mock_multiprocessing, *_):
        proxy_logger = log.ProxyLogger()
        current_process = Mock()
        current_process.name = "ABC"
        current_process.pid = 123
        mock_multiprocessing.current_process.return_value = current_process
        mock_threading.current_thread.side_effect = Exception
        self.assertEqual("(process ID ABC [PID 123])", proxy_logger.get_identifier())

    @patch("enmutils.lib.log.os.getpid", return_value=99999)
    @patch("enmutils.lib.log.multiprocessing")
    @patch("enmutils.lib.log.threading")
    def test_get_identifier__in_proxylogger_returns_pid_if_mainprocess_of_multiprocessing(
            self, mock_threading, mock_multiprocessing, *_):
        proxy_logger = log.ProxyLogger()
        current_process = Mock()
        current_process.name = "MainProcess"
        mock_multiprocessing.current_process.return_value = current_process
        mock_threading.current_thread.side_effect = Exception
        self.assertEqual("(PID 99999)", proxy_logger.get_identifier())

    @patch("enmutils.lib.log.os.getpid", return_value=99999)
    @patch("enmutils.lib.log.multiprocessing")
    @patch("enmutils.lib.log.threading")
    def test_get_identifier__in_proxylogger_returns_id_of_main_process(self, mock_threading, mock_multiprocessing, *_):
        proxy_logger = log.ProxyLogger()
        mock_multiprocessing.current_process.side_effect = Exception
        mock_threading.current_thread.side_effect = Exception
        self.assertEqual("(PID 99999)", proxy_logger.get_identifier())

    @patch("enmutils.lib.log.mutexer")
    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_log_cmd__is_successful_no_output(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.log_cmd("ABC", "1", "")
        self.assertTrue(call(['DEBUG', 'ABC', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '  Command return code: 1', 'caller_123', 'PID 9999'])
                        in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '  Command produced no output', 'caller_123', 'PID 9999'])
                        in mock_queue.put.mock_calls)

    @patch("enmutils.lib.log.mutexer")
    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_log_cmd__is_successful_with_one_line_output(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.log_cmd("ABC", "1", "X")
        self.assertTrue(call(['DEBUG', 'ABC', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '  Command return code: 1', 'caller_123', 'PID 9999'])
                        in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '  Command output: X', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)

    @patch("enmutils.lib.log.mutexer")
    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_log_cmd__is_successful_more_lines_output(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.log_cmd("ABC", "1", "X\nY")
        self.assertTrue(call(['DEBUG', 'ABC', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '  Command return code: 1', 'caller_123', 'PID 9999'])
                        in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '  Command output: ', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '    X', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', '    Y', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)

    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_debug__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.debug("message")
        mock_queue.put.assert_called_with(['DEBUG', 'message', 'caller_123', 'PID 9999'])

    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_info__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.info("message")
        mock_queue.put.assert_called_with(['INFO', 'message', 'caller_123', 'PID 9999'])

    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_warn__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.warn("message")
        mock_queue.put.assert_called_with(['WARNING', 'message', 'caller_123', 'PID 9999'])

    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_rest__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.rest("message")
        mock_queue.put.assert_called_with(['REST', 'message', 'caller_123', 'PID 9999'])

    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_error__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.error("message")
        mock_queue.put.assert_called_with(['ERROR', 'message', 'caller_123', 'PID 9999'])

    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_syslog__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.syslog("message")
        mock_queue.put.assert_called_with(['SYSLOG', 'message', 'caller_123', 'PID 9999'])

    @patch("enmutils.lib.log.os.getpid", return_value=9999)
    @patch("enmutils.lib.log.persistence.publish")
    def test_workload__is_successful(self, mock_publish, *_):
        proxy_logger = log.ProxyLogger()
        proxy_logger.workload("MAJOR", "PM_01", "some_msg")
        mock_publish.assert_called_with('workload-log', 'MAJOR||||PM_01||||9999||||some_msg')

    @patch("enmutils.lib.log.mutexer")
    @patch("enmutils.lib.log.ProxyLogger.get_identifier", return_value="PID 9999")
    @patch("enmutils.lib.log.ProxyLogger.get_caller", return_value="caller_123")
    def test_exception__is_successful(self, *_):
        mock_queue = Mock()
        log.log_queue = mock_queue
        proxy_logger = log.ProxyLogger()
        proxy_logger.exception(["message1"])
        self.assertTrue(call(['EXCEPTION', 'message1', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)
        self.assertTrue(call(['DEBUG', 'message1', 'caller_123', 'PID 9999']) in mock_queue.put.mock_calls)

    @patch('enmutils.lib.log.config.get_log_dir', return_value="path")
    @patch('enmutils.lib.log.log_mgr.MultiProcessingLog.__init__', return_value=None)
    @patch('enmutils.lib.log.log_mgr.MultiProcessingLog.setFormatter')
    def test_get_workload_ops_logger__returns_logger_instance(self, *_):
        self.assertIsInstance(log.get_workload_ops_logger("module"), logging.Logger)

    @patch('enmutils.lib.log.os.getpid', return_value=9999)
    @patch('enmutils.lib.log.persistence.publish')
    def test_log_workload__successful(self, mock_publish, _):
        log.log_workload(None, "MAJOR", "PM_01", "some_msg")
        mock_publish.assert_called_with('workload-log', 'MAJOR||||PM_01||||9999||||some_msg')

    def test_get_log_level_color__all(self):
        val = log.get_log_level_color(level="ALL WARN TRACE DEBUG INFO ", text="print statement")
        self.assertEqual(val, "\033[95mprint statement\x1b[0m")

    def test_get_log_level_color__warn(self):
        val = log.get_log_level_color(level="WARN", text="print statement")
        self.assertEqual(val, "\x1b[33mprint statement\x1b[0m")

    def test_get_log_level_color__trace(self):
        val = log.get_log_level_color(level="TRACE", text="some_text")
        self.assertEqual(val, "\033[97msome_text\033[0m")

    def test_get_log_level_color__debug(self):
        val = log.get_log_level_color(level="DEBUG", text="some_text")
        self.assertEqual(val, "\033[97msome_text\033[0m")

    def test_get_log_level_color__INFO(self):
        val = log.get_log_level_color(level="INFO", text="some_text")
        self.assertEqual(val, "\033[96msome_text\033[0m")

    def test_get_log_level_color__error(self):
        val = log.get_log_level_color(level="ERROR", text="some_text")
        self.assertEqual(val, "\033[91msome_text\033[0m")

    def test_get_log_level_color__fatal(self):
        val = log.get_log_level_color(level="FATAL", text="some_text")
        self.assertEqual(val, "\033[91msome_text\033[0m")

    def test_get_log_level_color__other(self):
        val = log.get_log_level_color(level="ABC", text="some_text")
        self.assertEqual(val, "some_text")

    def test_get_profiles_logger__returns_logger_instance(self):
        log.get_profiles_logger()

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_red_text__successfull(self, _):
        log.red_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_red_text__unsuccessfull(self, _):
        log.red_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_yellow_text__successfull(self, _):
        log.yellow_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_yellow_text__unsuccessfull(self, _):
        log.yellow_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_blue_text__successfull(self, _):
        log.blue_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_blue_text__unsuccessfull(self, _):
        log.blue_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_green_text__successfull(self, _):
        log.green_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_green_text__unsuccessfull(self, _):
        log.green_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_purple_text__successfull(self, _):
        log.purple_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_purple_text__unsuccessfull(self, _):
        log.purple_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_cyan_text__successfull(self, _):
        log.cyan_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_cyan_text__unsuccessfull(self, _):
        log.cyan_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_white_text__successfull(self, _):
        log.white_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_white_text__unsuccessfull(self, _):
        log.white_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=True)
    def test_underline_text__successfull(self, _):
        log.underline_text("some_text")

    @patch('enmutils.lib.log._check_use_color', return_value=False)
    def test_underline_text__unsuccessfull(self, _):
        log.underline_text("some_text")

    def test_console_log_http_request__headers(self):
        mock_request = Mock()
        mock_response = Mock()
        log.console_log_http_request(mock_request, mock_response)

    @patch('enmutils.lib.log.logger')
    @patch('enmutils.lib.log.inspect.stack', return_value=[])
    def test_log_entry__stack_equals_to_zero(self, *_):
        log.log_entry()

    def test_console_log_http_request__if_cond(self):
        mock_request = Mock()
        mock_request.headers = None
        mock_request.data = None
        mock_request.json = None
        mock_request.params = None
        log.console_log_http_request(mock_request, Mock())

    @patch('enmutils.lib.log.os.path.isdir', return_value=True)
    def test_prepare_log_dir__if_cond(self, _):
        log._prepare_log_dir("some_log_path")

    @patch('enmutils.lib.log.threading.Thread.start')
    def test_start__spinner_start(self, _):
        spinner = log.Spinner()
        spinner.start()

    def test_log_cmd__if_cond(self):
        log.log_cmd(Mock(), "print", "output", None)

    @patch('enmutils.lib.log.threading.Thread.join')
    def test_stop__spinner_stop(self, _):
        lag = log.Spinner()
        lag.stop()

    @patch("enmutils.lib.log.Spinner.__init__", return_value=None)
    @patch('enmutils.lib.log.sys.stdout')
    @patch('enmutils.lib.log.time.sleep')
    def test_init_spin__success(self, *_):
        spinner = log.Spinner()
        mock_run = spinner.stop_running = Mock()
        mock_run.is_set.side_effect = [False, True]
        spinner.init_spin()

    def test_log_entry__not_logger(self):
        log.logger = None
        log.log_entry("some_parameter")

    @patch('enmutils.lib.log.inspect.stack', return_value=['1', '2345'])
    def test_log_entry__calling_module_none(self, _):
        log.log_entry("some_parameter")

    @patch('enmutils.lib.log.inspect.stack')
    def test_log_entry__logs_exception(self, mock_stack):
        mock_stack.side_effect = IndexError
        log.log_entry("string")
        self.assertTrue(mock_stack.call_count, 1)
        self.assertEqual(log.logger.debug.call_count, 2)

    @patch('enmutils.lib.log.logging.shutdown')
    @patch('enmutils.lib.log.logger')
    def test_shutdown_handlers__break_successful(self, mock_logger, mock_shutdowm):
        mock_logger.handlers = mock_handlers = [Mock()]
        mock_handlers[0].name = "abc"
        log.shutdown_handlers(identifier="abc")
        self.assertEqual(mock_shutdowm.call_count, 1)
        self.assertEqual(mock_logger.removeHandler.call_count, 1)

    def test_log_exception__succesful(self):
        log.log_exception(Mock(), ['abc', 'def'])

    def test_log_syslog__successful(self):
        log.log_syslog(Mock(), "message")

    @patch('enmutils.lib.log.mutexer.mutex')
    @patch('enmutils.lib.log.logger.debug')
    def test_log_cmd__no_output(self, *_):
        log.log_cmd(Mock(), "print", "output", "")

    @patch('enmutils.lib.log.mutexer.mutex')
    @patch('enmutils.lib.log.logger.debug')
    def test_log_cmd__successful_output(self, *_):
        log.log_cmd(Mock(), "print", "output", "success")

    @patch('enmutils.lib.log.mutexer.mutex')
    @patch('enmutils.lib.log.logger.debug')
    def test_log_cmd__multiple_lines(self, *_):
        log.log_cmd(Mock(), "print", "output", "success\nsuccessful\nsuccessfully")

    def test_log_entry__none_parameters(self):
        log.log_entry(parameters=None)

    @patch('enmutils.lib.log.logger.debug')
    def test_log_console_flash_message__successful(self, _):
        log.log_console_flash_message("some_log_message")

    def test_clear_underline__successful(self):
        log.clear_underline("message")

    def test_clear_colors__successful(self):
        log.clear_colors("message")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
