import unittest2
from mock import patch, Mock

from enmutils.lib import exception
from testslib import unit_test_utils


class ExceptionUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.exception.init.exit")
    def test_handle_invalid_argument__is_None_sucess(self, mock_exit):
        exception.handle_invalid_argument(None)
        self.assertTrue(mock_exit.called)

    @patch("enmutils.lib.exception.init.exit")
    def test_handle_invalid_argument__not_None_sucess(self, mock_exit):
        exception.handle_invalid_argument("test")
        self.assertTrue(mock_exit.called)

    @patch("enmutils.lib.exception.init.exit")
    def test_handle_exception__success(self, mock_exit):
        exception.handle_exception("tool", "test", 5)
        self.assertTrue(mock_exit.called)

    @patch("enmutils.lib.exception.init.exit")
    @patch("enmutils.lib.exception.process_exception")
    @patch("enmutils.lib.exception.sys.exc_info")
    def test_handle_exception__not_None(self, mock_exc_info, mock_process, mock_exit):
        test_name = Mock(__name__="name")
        mock_exc_info.return_value = (test_name, test_name, Mock())
        exception.handle_exception("tool", None, 0)
        self.assertTrue(mock_process.called)

    @patch("enmutils.lib.exception.log.logger.exception")
    @patch("enmutils.lib.exception.cache.has_key")
    def test_process_exception__success(self, mock_has_key, mock_exception):
        mock_has_key.return_value = False
        exception.process_exception(None, False, False)
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.exception.traceback.extract_tb")
    @patch("enmutils.lib.exception.log.logger.exception")
    @patch("enmutils.lib.exception.cache.has_key")
    @patch("enmutils.lib.exception.sys.exc_info")
    def test_process_exception__not_None(self, mock_exc_info, mock_has_key, mock_exception, mock_tb):
        mock_has_key.return_value = False
        test_name = Mock(__name__="name")
        mock_exc_info.return_value = (test_name, "s", "t")
        mock_tb.return_value = [("f1", "2", "<module>", "45", "s"), ("f2", "5", "<package>", "34"),
                                ("f3", "7", "<module>", None, None), ("f4", "7"), ("f5", "72")]
        exception.process_exception("test", False, False)
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.exception.traceback.extract_tb")
    @patch("enmutils.lib.exception.log.logger.exception")
    @patch("enmutils.lib.exception.cache.has_key")
    @patch("enmutils.lib.exception.sys.exc_info")
    def test_process_exception__traceback_is_None(self, mock_exc_info, mock_has_key, mock_exception, mock_tb):
        mock_has_key.return_value = False
        test_name = Mock(__name__="name")
        mock_exc_info.return_value = (test_name, "s", None)
        mock_tb.return_value = [("f1", "2", "<package>", "45", "s"), ("f2", "5", "<package>", "34"),
                                ("f3", "7", "<package>", None, None), ("f4", "7"), ("f5", "72")]
        exception.process_exception("test", False, False)
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.exception.log.logger.error")
    @patch("enmutils.lib.exception.traceback.extract_tb")
    @patch("enmutils.lib.exception.log.logger.exception")
    @patch("enmutils.lib.exception.cache.has_key")
    @patch("enmutils.lib.exception.sys.exc_info")
    def test_process_exception__traceback_None(self, mock_exc_info, mock_has_key, mock_exception, mock_tb, mock_error):
        mock_has_key.return_value = False
        test_name = Mock(__name__="name")
        mock_obj = Mock()
        mock_obj.return_value = None
        mock_exc_info.return_value = (test_name, "s", mock_obj)
        mock_tb.return_value = [("f1", "2", "<package>", "45", "s"), ("f2", "5", "<package>", "34"),
                                ("f3", "7", "<package>", None, None), ("f4", "7"), ("f5", "72")]
        exception.process_exception("test", False, True)
        self.assertTrue(mock_error.called)

    @patch("enmutils.lib.exception.init.exit")
    @patch("enmutils.lib.exception.traceback.extract_tb")
    @patch("enmutils.lib.exception.log.logger.exception")
    @patch("enmutils.lib.exception.cache.has_key")
    @patch("enmutils.lib.exception.sys.exc_info")
    def test_process_excpetion__shutdown_success(self, mock_exc_info, mock_has_key, mock_exception, mock_tb, mock_exit):
        mock_has_key.return_value = False
        test_name = Mock(__name__="name")
        mock_exc_info.return_value = (test_name, "s", None)
        mock_tb.return_value = [("f1", "2", "<package>", "45", "s"), ("f2", "5", "<package>", "34"),
                                ("f3", "7", "<package>", None, None), ("f4", "7"), ("f5", "72")]
        exception.process_exception("test", True, False)
        self.assertTrue(mock_exit.called)

    @patch("enmutils.lib.exception.cache.has_key")
    def test_process_exception__return_none(self, mock_has_key):
        mock_has_key.return_value = True
        self.assertEqual(exception.process_exception("test", True, False), None)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
