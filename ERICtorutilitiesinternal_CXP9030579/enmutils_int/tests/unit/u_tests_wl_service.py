#!/usr/bin/env python

import sys

import unittest2
from flask import Flask
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase

import enmutils_int.bin.wl_service as tool
import enmutils_int.lib.services.default_routes as default_routes
from testslib import unit_test_utils

TOOL_NAME = "wl_service.py"
app = Flask(__name__)


class ServiceUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.request_environ = {'SERVER_SOFTWARE': 'waitress', 'SCRIPT_NAME': '', 'REQUEST_METHOD': 'GET',
                                'PATH_INFO': '/status', 'SERVER_PROTOCOL': 'HTTP/1.1', 'QUERY_STRING': '',
                                'REMOTE_ADDR': 'some_remote_ip', 'HTTP_USER_AGENT': 'curl blah',
                                'SERVER_NAME': 'cloud-ms-1', 'REMOTE_PORT': '51386', 'wsgi.url_scheme': 'http',
                                'SERVER_PORT': '5002', 'werkzeug.request': Mock(), 'wsgi.input': Mock(),
                                'HTTP_HOST': 'localhost:5002', 'wsgi.multithread': True, 'HTTP_ACCEPT': '*/*',
                                'wsgi.version': (1, 0), 'wsgi.run_once': False, 'wsgi.errors': Mock(),
                                'wsgi.multiprocess': False,
                                'wsgi.file_wrapper': Mock(), 'REMOTE_HOST': 'some_remote_host',
                                'wsgi.input_terminated': True}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('sys.exit')
    @patch("enmutils_int.bin.wl_service.initialize_logger")
    @patch("enmutils_int.bin.wl_service.service_registry.get_registry_data",
           return_value={"usermanager": {"port": 5001}})
    @patch("docopt.extras")
    @ParameterizedTestCase.parameterize(
        ("mock_arguments",),
        [
            ([TOOL_NAME],),
            ([TOOL_NAME, "-h"],),
            ([TOOL_NAME, "blah"],),
            ([TOOL_NAME, "usermanager", "blah"],),
            ([TOOL_NAME, "other", "start"],),
        ]
    )
    def test_cli__handles_invalid_args_successfully(self, mock_arguments, *_):
        sys.argv = mock_arguments
        self.assertRaises(SystemExit, tool.cli)

    @patch('sys.exit')
    @patch("enmutils_int.bin.wl_service.initialize_logger")
    @patch("docopt.extras")
    @patch("flask.app.Flask.register_blueprint")
    @patch("enmutils_int.bin.wl_service.start")
    @patch("enmutils_int.bin.wl_service.status")
    @patch("enmutils_int.bin.wl_service.service_registry.get_registry_data",
           return_value={"usermanager": {"port": 5001}})
    @ParameterizedTestCase.parameterize(
        ("mock_arguments",),
        [
            ([TOOL_NAME, "usermanager"],),
            ([TOOL_NAME, "usermanager", "status"],),
        ]
    )
    def test_cli__handles_valid_args_successfully(self, mock_arguments, *_):
        sys.argv = mock_arguments
        self.assertEqual(0, tool.cli())

    @patch("enmutils_int.bin.wl_service.initialize_logger")
    @patch("enmutils_int.bin.wl_service.get_arguments", return_value=("some_service", "start"))
    @patch("enmutils_int.bin.wl_service.start", side_effect=Exception("cant start"))
    def test_cli__raises_runtimeerror_if_service_cannot_start(self, *_):
        with self.assertRaises(SystemExit) as error:
            tool.cli()
        self.assertEqual("cant start", error.exception.message)

    @patch("logging.handlers.WatchedFileHandler")
    @patch("logging.Formatter")
    @patch("logging.StreamHandler")
    @patch("commands.getoutput")
    @patch("logging.getLogger")
    def test_initialize_logger__is_successful(self, mock_getlogger, *_):
        tool.initialize_logger("blah")
        self.assertEqual(2, mock_getlogger.return_value.addHandler.call_count)

    @patch("logging.handlers.WatchedFileHandler")
    @patch("logging.Formatter")
    @patch("logging.StreamHandler")
    @patch("commands.getoutput")
    @patch("logging.getLogger")
    def test_log_message__is_successful_if_logger_is_set(self, mock_logger, *_):
        tool.initialize_logger("usermanager")
        tool.log_message("blah")
        mock_logger.return_value.debug.assert_called_with("blah")

    @patch("enmutils_int.bin.wl_service.get_service_name_from_running_service")
    @patch("logging.handlers.WatchedFileHandler")
    @patch("logging.Formatter")
    @patch("logging.StreamHandler")
    @patch("commands.getoutput")
    @patch("logging.getLogger")
    def test_log_message__is_successful_if_logger_is_not_set(self, mock_getlogger, *_):
        tool.service_logger = None
        tool.log_message("blah")
        mock_getlogger.return_value.debug.assert_called_with("blah")

    @patch("enmutils_int.lib.services.default_routes.log_message")
    def test_handle_error__is_successful(self, *_):
        some_error = Exception("Test Error")
        self.assertEqual("Error encountered: Test Error", default_routes.handle_error(some_error))

    @patch("enmutils_int.bin.wl_service.service_registry.get_service_name_for_service_port", return_value="usermanager")
    @patch("enmutils_int.bin.wl_service.request")
    def test_get_service_name_from_running_service__is_successful_if_service_found(self, mock_request, *_):
        mock_request.environ.get.return_value = "5001"
        self.assertEqual("usermanager", tool.get_service_name_from_running_service())

    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           return_value=(5001, "localhost", 10))
    @patch("commands.getoutput")
    def test_status__is_successful_when_service_is_running(self, mock_getoutput, *_):
        mock_getoutput.return_value = "is running"
        self.assertEqual("is running", tool.status("usermanager"))

    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           return_value=(5001, "localhost", 10))
    @patch("commands.getoutput")
    def test_status__raises_runtimeerror_when_service_is_not_running(self, mock_getoutput, *_):
        mock_getoutput.return_value = ""
        with self.assertRaises(RuntimeError) as error:
            tool.status("usermanager")
        self.assertEqual(error.exception.message, "Service usermanager not running")

    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           return_value=(5001, "localhost", 10))
    @patch("commands.getoutput")
    def test_status__raises_runtimeerror_when_service_is_not_responding(self, mock_getoutput, *_):
        mock_getoutput.return_value = "timed out"
        cmd = 'curl -m5 -Ss "http://localhost:5001/status" 2>&1'
        message = ("Problem encountered checking usermanager status. Attempted to run command: '{0}'. "
                   "Result: timed out".format(cmd))
        with self.assertRaises(RuntimeError) as error:
            tool.status("usermanager")
        self.assertEqual(error.exception.message, message)

    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           return_value=(5001, "localhost", 10))
    @patch("commands.getoutput")
    def test_status__raises_runtimeerror_when_checking_service(self, mock_getoutput, *_):
        mock_getoutput.side_effect = Exception("some problem")
        cmd = 'curl -m5 -Ss "http://localhost:5001/status" 2>&1'
        message = ("Problem encountered checking usermanager status. Attempted to run command: '{0}'. "
                   "Result: some problem".format(cmd))
        with self.assertRaises(RuntimeError) as error:
            tool.status("usermanager")
        self.assertEqual(error.exception.message, message)

    @patch("enmutils_int.bin.wl_service.config.load_config")
    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.initial_request")
    @patch("enmutils_int.bin.wl_service.initialize_logger")
    @patch("enmutils_int.bin.wl_service.initialize_webserver")
    @patch("commands.getoutput")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           return_value=(5001, "localhost", 12))
    @patch("enmutils_int.bin.wl_service.serve")
    def test_start__is_successful(self, mock_serve, *_):
        mock_app = Mock()
        tool.app = mock_app
        tool.service_logger = Mock(handlers=[Mock(), Mock()])
        tool.start("usermanager")
        mock_serve.assert_called_with(mock_app, port=5001, threads=12)

    @patch("enmutils_int.bin.wl_service.config.load_config")
    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.initial_request")
    @patch("enmutils_int.bin.wl_service.initialize_logger")
    @patch("enmutils_int.bin.wl_service.initialize_webserver")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           return_value=(5001, "localhost", 10))
    @patch("enmutils_int.bin.wl_service.serve")
    def test_start__is_unsuccessful_if_service_already_running(self, mock_serve, *_):
        mock_app = Mock()
        tool.app = mock_app
        mock_serve.side_effect = Exception("Address already in use")
        tool.service_logger = Mock(handlers=[Mock(), Mock()])
        with self.assertRaises(RuntimeError) as error:
            tool.start("usermanager")
        self.assertEqual(error.exception.message, "Service usermanager already running")
        mock_serve.assert_called_with(mock_app, port=5001, threads=10)

    @patch("enmutils_int.bin.wl_service.config.load_config")
    @patch("enmutils_int.bin.wl_service.log_message")
    @patch("enmutils_int.bin.wl_service.initialize_logger")
    @patch("enmutils_int.bin.wl_service.initial_request")
    @patch("enmutils_int.bin.wl_service.initialize_webserver")
    @patch("enmutils_int.bin.wl_service.service_registry.get_service_info_for_service_name",
           side_effect=RuntimeError("Service testservice not defined in registry"))
    @patch("enmutils_int.bin.wl_service.serve")
    def test_start__is_unsuccessful_if_service_not_in_registry(self, *_):
        with self.assertRaises(RuntimeError) as error:
            tool.start("testservice")
        self.assertEqual(error.exception.message, "Service testservice not defined in registry")

    @patch('enmutils_int.bin.wl_service.log_message')
    @patch('enmutils_int.bin.wl_service.importlib.import_module')
    def test_initial_request__only_apply_if_at_start_up_function(self, mock_import_module, _):
        with app.test_request_context():
            mock_import_module.return_value.at_startup = None
            tool.app = Mock()
            tool.initial_request("testservice")
            self.assertEqual(0, tool.app.before_first_request.call_count)

    @patch('enmutils_int.bin.wl_service.log_message')
    @patch('enmutils_int.bin.wl_service.importlib.import_module')
    def test_initial_request__calls_trigger(self, *_):
        with app.test_request_context():
            tool.app = Mock()
            tool.initial_request("testservice")
            self.assertEqual(1, tool.app.try_trigger_before_first_request_functions.call_count)

    @patch("time.time")
    @patch("threading.current_thread")
    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils_int.lib.services.default_routes.request")
    def test_log_application_request__is_successful_if_status_request_received(
            self, mock_request, mock_debug, mock_current_thread, *_):
        mock_request.environ = self.request_environ
        mock_request.get_json.return_value = "some_json_content"
        default_routes.log_application_request()
        self.assertFalse(mock_debug.called)
        self.assertFalse(mock_current_thread.called)

    @patch("threading.current_thread")
    @patch("time.time")
    @patch("enmutils.lib.log.logger.debug")
    @patch("enmutils_int.lib.services.default_routes.request")
    def test_log_application_request__is_successful_if_non_status_request_received(self, mock_request, mock_debug, *_):
        mock_request.environ = {'SERVER_SOFTWARE': 'waitress', 'SCRIPT_NAME': '', 'REQUEST_METHOD': 'POST',
                                'PATH_INFO': '/api/v1/users/create', 'SERVER_PROTOCOL': 'HTTP/1.1', 'QUERY_STRING': '',
                                'REMOTE_ADDR': 'some_ip_address', 'CONTENT_LENGTH': '96',
                                'HTTP_USER_AGENT': 'python-requests/2.6.0 CPython/2.7.8 Linux/2.6.32-504.el6.x86_64',
                                'HTTP_CONNECTION': 'keep-alive', 'SERVER_NAME': 'ieatwlvm7004', 'REMOTE_PORT': '60715',
                                'wsgi.url_scheme': 'http', 'SERVER_PORT': '5001', 'werkzeug.request': Mock(),
                                'wsgi.input': Mock(), 'HTTP_HOST': 'localhost:5001', 'wsgi.multithread': True,
                                'HTTP_ACCEPT': '*/*', 'wsgi.version': (1, 0), 'wsgi.run_once': False,
                                'wsgi.errors': Mock(), 'wsgi.multiprocess': False, 'CONTENT_TYPE': 'application/json',
                                'wsgi.file_wrapper': Mock(), 'REMOTE_HOST': 'some_ip_address',
                                'HTTP_ACCEPT_ENCODING': 'gzip, deflate', 'wsgi.input_terminated': True}
        mock_request.get_json.return_value = "some_json_content"
        default_routes.log_application_request()
        self.assertTrue(call("Request received: {0}".format(mock_request.environ)) in mock_debug.mock_calls)
        self.assertTrue(call("Data received in request: some_json_content") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.services.default_routes.log_message")
    @patch("enmutils_int.lib.services.default_routes.get_service_name_from_running_service", return_value="service1")
    @patch("enmutils_int.lib.services.default_routes.request")
    def test_server_status__is_successful(self, mock_request, *_):
        mock_request.environ = self.request_environ
        message = "Webserver for Workload Service service1 is running and listening on port: 5002"
        self.assertEqual(message, default_routes.server_status())

    @patch("enmutils_int.bin.wl_service.initialize_application_logger")
    @patch("enmutils_int.bin.wl_service.Flask")
    @patch("enmutils_int.bin.wl_service.register_blueprints")
    def test_initialize_webserver__is_successful(self, mock_register, *_):
        tool.initialize_webserver("usermanager")
        self.assertEqual(1, mock_register.call_count)

    @patch("enmutils_int.bin.wl_service.register_view_functions")
    @patch("enmutils_int.bin.wl_service.register_swagger_blueprint")
    @patch("enmutils_int.bin.wl_service.initialize_application_logger")
    def test_register_blueprints__is_successful(self, *_):
        tool.app = Mock()
        tool.register_blueprints("usermanager")

    def test_register_blueprints__raises_runtimeerror_if_cant_register_default_blueprint(self, *_):
        tool.app = Mock()
        tool.app.register_blueprint.side_effect = Exception("error during registration")
        with self.assertRaises(RuntimeError) as error:
            tool.register_blueprints("usermanager")
        self.assertEqual(error.exception.message, "Error registering default blueprint: error during registration")

    @patch("enmutils_int.bin.wl_service.register_view_functions")
    def test_register_blueprints__raises_runtimeerror_if_cant_register_application_blueprint(self, *_):
        tool.app = Mock()
        tool.app.register_blueprint.side_effect = [None, Exception("error during registration")]
        with self.assertRaises(RuntimeError) as error:
            tool.register_blueprints("usermanager")
        self.assertEqual(error.exception.message, "Error registering application blueprint: error during registration")

    @patch("enmutils.lib.log.simplified_log_init")
    def test_initialize_application_logger__is_successful_if_logger_exists(self, mock_simplified_log_init, *_):
        tool.log.logger = Mock()
        tool.initialize_application_logger("usermanager")
        self.assertFalse(mock_simplified_log_init.called)

    @patch("enmutils.lib.log.simplified_log_init")
    def test_initialize_application_logger__is_successful_if_logger_doesnt_exist(self, mock_simplified_log_init, *_):
        tool.log.logger = None
        tool.initialize_application_logger("usermanager")
        self.assertTrue(mock_simplified_log_init.called)
        tool.log.logger = Mock()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
