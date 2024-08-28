import unittest2
from mock import patch, Mock

from enmutils.lib import init
from testslib import unit_test_utils


class InitUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.init.log.logger")
    @patch("enmutils.lib.init.log.logger.warn")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.log.yellow_text")
    def test_alarm_handler__yellow_text_success(self, mock_yellow, *_):
        init._alarm_handler("s", "t", None)
        self.assertFalse(mock_yellow.called)

    @patch("enmutils.lib.init.exit")
    def test_alarm_handler__logger_None(self, _):
        init.log.logger = None
        init._alarm_handler("init", dummy="abc")

    @patch("enmutils.lib.init.signal.alarm")
    def test_set_timeout__success(self, mock_alarm):
        init._set_timeout("5", "test")
        self.assertTrue(mock_alarm.called)

    @patch("enmutils.lib.exception.process_exception")
    def test_set_timeout__exception_raised(self, mock_exception):
        with self.assertRaises(TypeError) as m:
            init._set_timeout("5.2", "test")
        the_exception = m.exception
        self.assertTrue(the_exception)

    @patch("enmutils.lib.log.logger", return_value=None)
    @patch("enmutils.lib.init.log.logger.warn")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.log.yellow_text")
    def test_signal_handler__success(self, mock_yellow, mock_exit, mock_log, *_):
        init.signal_handler("s", "h", None)
        self.assertTrue(mock_exit.called)

    @patch("enmutils.lib.init.exit")
    def test_signal_handler__logger_None(self, _):
        init.log.logger = None
        init.signal_handler("init", dummy="abc")

    @patch("enmutils.lib.multitasking.terminate_threads")
    @patch("enmutils.lib.mutexer.terminate_mutexes")
    @patch("enmutils.lib.init.os._exit")
    @patch("enmutils.lib.log.log_shutdown")
    def test_exit__success(self, mock_log, *_):
        init.exit([5], None)
        self.assertTrue(mock_log.called)

    @patch("enmutils.lib.multitasking.terminate_threads", side_effect=Exception)
    @patch("enmutils.lib.init.os._exit")
    @patch("enmutils.lib.exception.process_exception")
    def test_exit__exception_by_terminate_mutexes(self, mock_exception, *_):
        init.exit("6", None)
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.multitasking.terminate_threads", side_effect=[Exception, Exception])
    @patch("enmutils.lib.init.os._exit")
    @patch("enmutils.lib.exception.process_exception")
    def test_exit__callback_is_not_None(self, mock_exception, *_):
        init.log.logger = None
        init.exit("6", Mock)
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.multitasking.terminate_threads", side_effect=Exception)
    @patch("enmutils.lib.init.os._exit")
    @patch("enmutils.lib.exception.process_exception")
    def test_exit__logger_is_None(self, mock_exception, *_):
        init.log.logger = None
        init.exit("5", "test")
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.persistence.default_db")
    def test_global_init__success(self, mock_default_db):
        init.global_init("func-test", "prod", "test")
        self.assertTrue(mock_default_db.called)

    @patch("enmutils.lib.log.simplified_log_init")
    @patch("enmutils.lib.persistence.default_db")
    def test_global_init__simplified_logging_success(self, mock_default_db, mock_log_init):
        init.global_init("fun-test", "prod", "test", None, True, 0)
        mock_log_init.assert_called_with('test')
        self.assertTrue(mock_default_db.called)

    @patch("enmutils.lib.init.os.makedirs")
    @patch("enmutils.lib.init.persistence.default_db")
    @patch("enmutils.lib.log.log_init")
    @patch("enmutils.lib.config.get_prop")
    def test_global_init__simplified_logging_not_success(self, mock_get_prop, mock_log_init, mock_default_db, *_):
        mock_get_prop.return_value = "dir2"
        init.global_init("fun-test", "prod", "test", None, False)
        self.assertTrue(mock_log_init.called)
        self.assertTrue(mock_default_db.called)

    @patch("enmutils.lib.init.multiprocessing.cpu_count")
    @patch("enmutils.lib.persistence.default_db")
    def test_global_init__cpu_tools_map_success(self, mock_default_db, mock_cpu_count):
        mock_cpu_count.return_value = 2
        with patch.dict("enmutils.lib.init.CPU_TOOLS_MAP", {"test": 5}):
            init.global_init("fun-test", "prod", "test", None, False)
            self.assertTrue(mock_default_db.called)

    @patch("enmutils.lib.config.load_config", side_effect=Exception)
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.log.red_text")
    def test_global_init__exception_by_load_config(self, mock_red_text, *_):
        init.global_init("fun-test", "prod", "test", None, False)
        self.assertTrue(mock_red_text.called)

    @patch("enmutils.lib.log.log_init", side_effect=Exception)
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.log.red_text")
    def test_global_init__exception_by_log_init(self, mock_red_text, *_):
        init.global_init("fun-test", "prod", "test", None, False)
        self.assertTrue(mock_red_text.called)

    @patch("enmutils.lib.init.log.logger.error")
    @patch("enmutils.lib.init.os.makedirs")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.log.log_init")
    @patch("os.path.exists", return_value=None)
    @patch("enmutils.lib.exception.process_exception", return_value=Mock())
    @patch("enmutils.lib.config.get_prop", return_value=None)
    def test_global_init__creating_new_general_directory(self, mock_get_prop, *_):
        mock_get_prop.return_value = "dir1"
        with self.assertRaises(Exception):
            init.global_init("fun-test", "prod", "test", None, False)

    @patch("enmutils.lib.init.config.get_prop")
    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.init.log.log_init")
    @patch("enmutils.lib.init.os")
    @patch("enmutils.lib.init.log")
    @patch("enmutils.lib.init.exception.process_exception")
    def test_global_init__exception_by_os_path_exists(self, mock_except, mock_log, mock_os, *_):
        mock_os.path.exists.side_effect = Exception
        init.global_init("fun-test", "prod", "test", None, False)
        self.assertEqual(mock_except.call_count, 1)
        self.assertEqual(mock_log.logger.error.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
