# !/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib import log_mgr

from enmutils.lib.log_mgr import UtilitiesLogManager, MultiProcessingLog, CompressedRotatingFileHandler
from testslib import unit_test_utils


class LogMgrUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.config.has_prop', return_value=True)
    @patch('enmutils.lib.config.get_prop')
    @patch('enmutils.lib.config.get_log_dir')
    @patch('enmutils.lib.log_mgr.logging')
    @patch('enmutils.lib.log_mgr.signal.signal')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.process_logs')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.__init__', return_value=None)
    def test_utilities_log_manager_init(self, *_):
        mock_queue = Mock()
        log_mgr = UtilitiesLogManager(queue={})
        log_mgr.queue = mock_queue
        log_mgr.init()

    @patch('enmutils.lib.config.has_prop', return_value=True)
    @patch('enmutils.lib.config.get_prop', return_value="debug")
    @patch('enmutils.lib.config.get_log_dir')
    @patch('enmutils.lib.log_mgr.logging')
    @patch("logging.Handler.setFormatter")
    @patch('enmutils.lib.log_mgr.signal.signal')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.process_logs')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.__init__', return_value=None)
    def test_utilities_log_manager_debug(self, *_):
        mock_queue = Mock()
        log_mgr = UtilitiesLogManager(queue={})
        log_mgr.queue = mock_queue
        log_mgr.init()

    @patch('enmutils.lib.config.has_prop', return_value=True)
    @patch('enmutils.lib.config.get_prop', return_value="warn")
    @patch('enmutils.lib.config.get_log_dir')
    @patch('enmutils.lib.log_mgr.logging')
    @patch("logging.Handler.setFormatter")
    @patch('enmutils.lib.log_mgr.signal.signal')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.process_logs')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.__init__', return_value=None)
    def test_utilities_log_manager_warn(self, *_):
        mock_queue = Mock()
        log_mgr = UtilitiesLogManager(queue={})
        log_mgr.queue = mock_queue
        log_mgr.init()

    @patch("enmutils.lib.log_mgr.UtilitiesLogManager.process_logs")
    def test_utilities_log_manager_init__success(self, _):
        queue = Mock()
        self.assertTrue(UtilitiesLogManager(queue={queue}))

    @patch("threading.Thread")
    @patch("multiprocessing.Queue")
    @patch("logging.handlers.WatchedFileHandler")
    @patch("logging.Handler")
    def test_multiprocessinglog(self, *_):
        MultiProcessingLog("")

    @patch('enmutils.lib.log_mgr.logging')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.process_logs')
    @patch('enmutils.lib.log_mgr.UtilitiesLogManager.__init__', return_value=None)
    @patch("logging.shutdown")
    def test_shutdown__success(self, mock_shutdown, *_):
        log_mgr = UtilitiesLogManager(queue={})
        log_mgr.shutdown()
        self.assertFalse(mock_shutdown.called)

    @patch("enmutils.lib.log_mgr.threading.Thread")
    @patch("enmutils.lib.log_mgr.multiprocessing.Queue")
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.logging.Handler.setFormatter")
    def test_setFormatter__success(self, mock_formatter, *_):
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.setFormatter(Mock())
        self.assertTrue(mock_formatter.called)

    @patch("enmutils.lib.log_mgr.threading.Thread")
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.multiprocessing.Queue")
    def test_send__success(self, *_):
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.send(Mock())

    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.logging.Handler.close")
    def test_close__success(self, mock_close, _):
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.close()
        self.assertTrue(mock_close.called)

    @patch("enmutils.lib.log_mgr.traceback.print_exc")
    @patch("enmutils.lib.log_mgr.threading.Thread")
    @patch("enmutils.lib.log_mgr.multiprocessing.Queue")
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler.emit", side_effect=SystemExit)
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler.__init__", return_value=None)
    def test_receive__success(self, *_):
        log_mgr = MultiProcessingLog("some_file_path")
        with self.assertRaises(SystemExit):
            log_mgr.receive()

    @patch("enmutils.lib.log_mgr.traceback.print_exc")
    @patch("enmutils.lib.log_mgr.threading.Thread")
    @patch("enmutils.lib.log_mgr.multiprocessing.Queue")
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler.emit", side_effect=EOFError)
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler.__init__", return_value=None)
    def test_receive__eof_error(self, *_):
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.receive()

    @patch("enmutils.lib.log_mgr.threading.Thread")
    @patch("enmutils.lib.log_mgr.multiprocessing.Queue")
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler.emit", side_effect=[Exception, EOFError])
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler.__init__", return_value=None)
    @patch("enmutils.lib.log_mgr.traceback.print_exc")
    def test_receive__other_error(self, mock_traceback, *_):
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.receive()
        self.assertTrue(mock_traceback.called)

    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog._format_record")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog.send")
    def test_emit__success(self, mock_send, *_):
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.emit(Mock())
        self.assertTrue(mock_send.called)

    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog._format_record")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog.send")
    def test_emit__system_exit_exception_raised(self, mock_send, mock_format_record, _):
        mock_format_record.side_effect = SystemExit
        log_mgr = MultiProcessingLog("some_file_path")
        with self.assertRaises(SystemExit):
            log_mgr.emit(Mock())

    @patch("enmutils.lib.log_mgr.MultiProcessingLog.send")
    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog._format_record")
    def test_emit__keyboard_interrupt_exception_raised(self, mock_format_record, *_):
        mock_format_record.side_effect = KeyboardInterrupt
        log_mgr = MultiProcessingLog("some_file_path")
        with self.assertRaises(KeyboardInterrupt):
            log_mgr.emit(Mock())

    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.logging.Handler.format")
    def test_format_record__success(self, mock_format, _):
        test_record = Mock()
        test_record.exc_info = "test info"
        test_record.msg = 6
        test_record.args = 2
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr._format_record(test_record)
        self.assertTrue(mock_format.called)

    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.logging.Handler.format")
    def test_format_record__empty_record(self, mock_format, _):
        test_record = Mock()
        test_record.exc_info = None
        test_record.args = None
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr._format_record(test_record)
        self.assertFalse(mock_format.called)

    @patch("enmutils.lib.log_mgr.logging.handlers.WatchedFileHandler")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog._format_record")
    @patch("enmutils.lib.log_mgr.MultiProcessingLog.send")
    def test_emit__general_exception_raised(self, mock_send, mock_format_record, _):
        mock_format_record.side_effect = Exception
        log_mgr = MultiProcessingLog("some_file_path")
        log_mgr.emit(Mock())
        self.assertFalse(mock_send.called)

    @patch("enmutils.lib.log_mgr.logging.handlers.RotatingFileHandler.__init__", return_value=None)
    @patch("enmutils.lib.log_mgr.logging.handlers.RotatingFileHandler.shouldRollover")
    @patch("enmutils.lib.log_mgr.logging.Handler.acquire")
    @patch("enmutils.lib.log_mgr.logging.Handler.release")
    def test_shouldRollover__success(self, mock_release, *_):
        log_mgr = CompressedRotatingFileHandler()
        log_mgr.shouldRollover(Mock())
        self.assertTrue(mock_release.called)

    @patch("enmutils.lib.log_mgr.CompressedRotatingFileHandler.__init__", return_value=None)
    def test_do_Rollover__backup_count_greater_than_zero(self, *_):
        rollover = log_mgr.CompressedRotatingFileHandler()
        rollover.stream = Mock()
        rollover.backupCount = 10
        rollover.baseFilename = "abc"
        rollover.delay = Mock()
        rollover.doRollover()

    @patch("enmutils.lib.log_mgr.CompressedRotatingFileHandler.__init__", return_value=None)
    def test_do_Rollover__success(self, *_):
        rollover = log_mgr.CompressedRotatingFileHandler()
        rollover.stream = None
        rollover.backupCount = 0
        rollover.baseFilename = "abc"
        rollover.delay = Mock()
        rollover.doRollover()

    @patch("enmutils.lib.log_mgr.CompressedRotatingFileHandler.__init__", return_value=None)
    @patch('__builtin__.open')
    @patch('enmutils.lib.log_mgr.os.path.exists', return_value=True)
    @patch('enmutils.lib.log_mgr.os.rename')
    @patch('enmutils.lib.log_mgr.os.remove')
    @patch('enmutils.lib.log_mgr.shutil.copyfileobj')
    def test_do_Rollover__os_path_exists(self, *_):
        rollover = log_mgr.CompressedRotatingFileHandler()
        rollover.stream = None
        rollover.backupCount = 2
        rollover.baseFilename = "abc"
        rollover.delay = None
        rollover.encoding = None
        rollover.mode = "r"
        rollover.doRollover()

    @patch("enmutils.lib.log_mgr.CompressedRotatingFileHandler.__init__", return_value=None)
    @patch('__builtin__.open')
    @patch('enmutils.lib.log_mgr.os.path.exists', side_effect=[True, False, False, False])
    @patch('enmutils.lib.log_mgr.os.rename')
    @patch('enmutils.lib.log_mgr.os.remove')
    @patch('enmutils.lib.log_mgr.shutil.copyfileobj')
    def test_do_Rollover__delay_is_False(self, *_):
        rollover = log_mgr.CompressedRotatingFileHandler()
        rollover.stream = None
        rollover.backupCount = 2
        rollover.baseFilename = "abc"
        rollover.delay = None
        rollover.encoding = None
        rollover.mode = "r"
        rollover.doRollover()

    @patch("enmutils.lib.log_mgr.logging.handlers.RotatingFileHandler.__init__", return_value=None)
    def test_CompressedRotatingFileHandler_init__success(self, *_):
        self.assertTrue(CompressedRotatingFileHandler())

    def test_init__success(self):
        mock_queue = Mock()
        mock_msg_decode = Mock()
        mock_msg_decode.decode.side_effect = UnicodeError
        mock_msg_encode = Mock()
        mock_msg_encode.decode.side_effect = UnicodeError
        mock_msg_encode.encode.side_effect = BaseException
        mock_queue.get.side_effect = [["DEBUG", mock_msg_decode, "CALLER"],
                                      ["EXCEPTION", "MSG", "CALLER"],
                                      ["EXCEPTION", mock_msg_encode, "CALLER"],
                                      ["INFO", "MSG", "CALLER"],
                                      ["WARNING", "MSG", "CALLER"],
                                      ["ERROR", "MSG", "CALLER"],
                                      ["SYSLOG", "MSG", "CALLER", "EXTRA"],
                                      ["OTHER", "MSG", "CALLER"],
                                      ["Test"],
                                      Exception]
        with self.assertRaises(Exception):
            UtilitiesLogManager(mock_queue)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
