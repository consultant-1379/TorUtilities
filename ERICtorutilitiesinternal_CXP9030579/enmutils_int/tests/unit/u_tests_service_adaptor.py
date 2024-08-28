#!/usr/bin/env python

import unittest2
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.services import service_adaptor
from mock import patch, Mock
from testslib import unit_test_utils


class ServiceAdaptorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.service = "usermanager"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.services.service_adaptor.service_registry.get_service_info_for_service_name",
           return_value=(Mock(), Mock(), Mock()))
    @patch("enmutils_int.lib.services.service_adaptor.requests.get")
    def test_send_request_to_service__is_successful_with_get(self, mock_get, _):
        mock_response = Mock()
        mock_get.return_value = mock_response
        self.assertEqual(mock_response, service_adaptor.send_request_to_service("GET", "http://some_url",
                                                                                self.service))

    @patch("enmutils_int.lib.services.service_adaptor.service_registry.get_service_info_for_service_name",
           return_value=(Mock(), Mock(), Mock()))
    @patch("enmutils_int.lib.services.service_adaptor.requests.delete")
    def test_send_request_to_service__is_successful_with_delete(self, mock_delete, _):
        mock_response = Mock()
        mock_delete.return_value = mock_response
        self.assertEqual(mock_response, service_adaptor.send_request_to_service("DELETE", "http://some_url",
                                                                                self.service))

    @patch("enmutils_int.lib.services.service_adaptor.service_registry.get_service_info_for_service_name",
           return_value=(Mock(), Mock(), Mock()))
    @patch("enmutils_int.lib.services.service_adaptor.requests.post")
    def test_send_request_to_service__is_successful_with_post(self, mock_post, _):
        mock_response = Mock()
        mock_post.return_value = mock_response
        self.assertEqual(mock_response, service_adaptor.send_request_to_service("POST", "http://some_url",
                                                                                self.service))

    @patch("enmutils_int.lib.services.service_adaptor.service_registry.get_service_info_for_service_name",
           return_value=(Mock(), Mock(), Mock()))
    @patch("time.sleep")
    @patch("enmutils_int.lib.services.service_adaptor.requests.get")
    @patch("enmutils_int.lib.services.service_adaptor.log.logger.debug")
    def test_send_request_to_service__raises_environerror_with_get_if_response_is_nok(self, mock_debug, mock_get, *_):
        text = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN"> '
                '<title>500 Internal Server Error</title> '
                '<h1>Internal Server Error</h1> '
                '<p>Could not create user(s), error encountered :: Error in execute_create_flow: Failed to make '
                'request, status code:: [404] Reason:: [Not Found]. - error encountered ::  - see usermanager service '
                'log for more details (/home/enmutils/services/usermanager.log)</p> ')
        mock_response_bad = Mock(ok=0, text=text, reason="Internal Error", url='localhost', status_code=500)
        mock_response_good = Mock(ok=200)
        mock_get.side_effect = [mock_response_bad, mock_response_bad, mock_response_good]
        self.assertEqual(mock_response_good, service_adaptor.send_request_to_service("GET", "http://some_url",
                                                                                     self.service))
        self.assertEqual(mock_get.call_count, 3)
        mock_debug.assert_any_call('Response NOK after sending request to service usermanager :: URL: localhost :: '
                                   'Status code: 500 :: Reason: Internal Error')
        mock_debug.assert_any_call('Details of error encountered by service: Could not create user(s), '
                                   'error encountered :: Error in execute_create_flow: Failed to make request, '
                                   'status code:: [404] Reason:: [Not Found]. - error encountered ::  - see usermanager'
                                   ' service log for more details (/home/enmutils/services/usermanager.log)'
                                   ' :: retrying in 30s ...')

    @patch("enmutils_int.lib.services.service_adaptor.service_registry.get_service_info_for_service_name",
           return_value=(Mock(), Mock(), Mock()))
    @patch("time.sleep")
    @patch("enmutils_int.lib.services.service_adaptor.requests.get")
    def test_send_request_to_service__raises_environerror_if_get_raises_exception(self, mock_get, *_):
        mock_response = Mock(ok=200)
        mock_get.side_effect = [Exception, Exception, mock_response]
        self.assertEqual(mock_response, service_adaptor.send_request_to_service("GET", "http://some_url",
                                                                                self.service))
        self.assertEqual(mock_get.call_count, 3)

    @patch("enmutils_int.lib.services.service_adaptor.is_service_running")
    @patch("enmutils_int.lib.services.service_adaptor.service_registry.can_service_be_used", return_value=True)
    def test_can_service_be_used__returns_true_if_service_can_be_used_for_profiles(self, mock_can_service_be_used, *_):
        profile = Mock()
        profile.IGNORE_SOA = False
        self.assertTrue(service_adaptor.can_service_be_used("some_service", profile))
        mock_can_service_be_used.assert_called_with("some_service", profile.priority)

    @patch("enmutils_int.lib.services.service_adaptor.is_service_running")
    @patch("enmutils_int.lib.services.service_adaptor.service_registry.can_service_be_used", return_value=True)
    def test_can_service_be_used__returns_true_if_service_cant_be_used(self, mock_can_service_be_used, *_):
        profile = Mock()
        profile.IGNORE_SOA = True
        self.assertFalse(service_adaptor.can_service_be_used("some_service", profile))
        self.assertFalse(mock_can_service_be_used.called)

    @patch("enmutils_int.lib.services.service_adaptor.is_service_running")
    @patch("enmutils_int.lib.services.service_adaptor.service_registry.can_service_be_used", return_value=True)
    def test_can_service_be_used__returns_true_if_service_can_be_used_for_tools(self, mock_can_service_be_used, *_):
        self.assertTrue(service_adaptor.can_service_be_used("some_service"))
        mock_can_service_be_used.assert_called_with("some_service", None)

    @patch("enmutils_int.lib.services.service_adaptor.log.logger.debug")
    @patch("enmutils_int.lib.services.service_adaptor.commands.getoutput")
    def test_is_service_running__returns_true_if_service_is_running(self, mock_getoutput, mock_debug):
        mock_getoutput.return_value = ("Process running for usermanager service with PID: 52928\n"
                                       "Checking status of service usermanager\n"
                                       "Service some_service is running and listening on port: 5001")
        self.assertTrue(service_adaptor.is_service_running("some_service"))
        self.assertFalse(mock_debug.called)

    @patch("enmutils_int.lib.services.service_adaptor.log.logger.debug")
    @patch("enmutils_int.lib.services.service_adaptor.commands.getoutput")
    def test_is_service_running__returns_false_if_service_is_not_running(self, mock_getoutput, mock_debug):
        mock_getoutput.return_value = ("Process not running for profilemanager service "
                                       "- check logs in /home/enmutils/services")
        self.assertFalse(service_adaptor.is_service_running("some_service"))
        mock_debug.assert_called_with("Warning: Service some_service is not running")

    def test_validate_response__is_successful(self):
        response = Mock()
        response.json.return_value = {"message": "abc", "success": True}
        self.assertEqual("abc", service_adaptor.validate_response(response))

    def test_validate_response__raises_environerror_if_request_is_unsuccessful(self):
        response = Mock(content="Unsupported parameter")
        response.json.return_value = {"message": "", "success": False}
        with self.assertRaises(EnvironError) as e:
            service_adaptor.validate_response(response)
        self.assertEqual(e.exception.message, "Request was unsuccessful: Unsupported parameter")

    @patch('enmutils_int.lib.services.service_adaptor.log.logger')
    def test_print_service_operation_message__success(self, mock_logger):
        response = Mock()
        response.json.return_value = {"success": True, "message": "I am a message"}
        service_adaptor.print_service_operation_message(response, mock_logger)
        mock_logger.info.assert_called_with("I am a message")

    @patch('enmutils_int.lib.services.service_adaptor.log.logger.info')
    def test_print_service_operation_message__only_prints_successful_response(self, mock_logger):
        response = Mock()
        response.ok = False
        service_adaptor.print_service_operation_message(response, mock_logger)
        self.assertEqual(0, mock_logger.info.call_count)

    @patch('enmutils_int.lib.services.service_adaptor.log.logger.info')
    def test_print_service_operation_message__raises_runtime_error(self, mock_logger):
        response = Mock(status_code=599)
        response.ok = False
        self.assertRaises(RuntimeError, service_adaptor.print_service_operation_message,
                          response, mock_logger)
        self.assertEqual(0, mock_logger.info.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
