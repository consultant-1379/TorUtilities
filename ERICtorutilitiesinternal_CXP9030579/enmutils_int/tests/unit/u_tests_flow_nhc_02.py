#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import Mock, patch
from requests.exceptions import HTTPError, ConnectionError
from enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow import Nhc02


class NHC02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nhc_02 = Nhc02()
        self.nhc_02.NUM_USERS = 1
        self.nhc_02.TIMEOUT = 30
        self.nhc_02.USER_ROLES = "Nhc_Administrator"
        self.nhc_02.SCHEDULED_DAYS = "THURSDAY"
        self.nhc_02.SCHEDULED_TIMES_STRINGS = ["04:30:00"]
        self.nhc_02.NHC_JOB_TIME = "05:00:00"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.create_nhc_request_body')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow_success(self, mock_keep_running, mock_create_users, mock_create_request,
                                                mock_sleep, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_user.post.return_value = mock_response
        mock_create_users.return_value = [mock_user]
        mock_create_request.return_value = {}
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.create_nhc_request_body')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow__get_time_raises_http_error(self, mock_keep_running, mock_create_users,
                                                                    mock_get_time, mock_add_error,
                                                                    mock_create_request, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_create_users.return_value = [mock_user]
        mock_get_time.side_effect = HTTPError()
        mock_create_request.return_value = {}
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow__get_time_raises_connection_error(self, mock_keep_running, mock_create_users,
                                                                          mock_get_time, mock_add_error, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_create_users.return_value = [mock_user]
        mock_get_time.side_effect = ConnectionError()
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow_add_exception_as_error_while_getting_time(self, mock_keep_running,
                                                                                  mock_create_users, mock_get_time,
                                                                                  mock_add_error, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_create_users.return_value = [mock_user]
        mock_get_time.side_effect = EnvironmentError
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.create_nhc_request_body')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow_raises_connection_error(self, mock_keep_running, mock_create_users,
                                                                mock_create_request, mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_user.post.side_effect = ConnectionError()
        mock_create_users.return_value = [mock_user]
        mock_create_request.return_value = {}
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.create_nhc_request_body')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow_raises_http_error(self, mock_keep_running, mock_create_users,
                                                          mock_create_request, mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, True, False]
        mock_user = Mock()
        mock_user.post.side_effect = [HTTPError(), Mock()]
        mock_create_users.return_value = [mock_user]
        mock_create_request.return_value = {}
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.create_nhc_request_body')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow_raises_exception(self, mock_keep_running, mock_create_users,
                                                         mock_create_request, mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, True, False]
        mock_user = Mock()
        mock_user.post.side_effect = [Exception, Mock()]
        mock_create_users.return_value = [mock_user]
        mock_create_request.return_value = {}
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.create_nhc_request_body')
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.create_users")
    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow.Nhc02.keep_running")
    def test_nhc_02_execute_nhc_02_flow_response_not_ok(self, mock_keep_running, mock_create_users, mock_create_request, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_response = Mock()
        mock_response.ok = False
        mock_user.post.return_value = mock_response
        mock_create_users.return_value = [mock_user]
        mock_create_request.return_value = {}
        self.nhc_02.execute_nhc_02_flow()
        self.assertTrue(mock_response.raise_for_status.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
