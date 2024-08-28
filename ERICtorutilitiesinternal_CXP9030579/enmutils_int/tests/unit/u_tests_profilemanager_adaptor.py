#!/usr/bin/env python

import unittest2
from mock import patch, Mock

from enmutils_int.lib.services.profilemanager_adaptor import (POST_METHOD, SET_STATUS_URL, SERVICE_NAME,
                                                              send_request_to_service, can_service_be_used, set_status,
                                                              ADD_EXCEPTION_URL, add_profile_exception, GET_STATUS_URL,
                                                              get_status, clear_profile_exceptions, CLEAR_ERRORS_URL,
                                                              clear_profile_pid_files, CLEAR_PIDS_URL, GET_PROFILES_URL,
                                                              get_all_profiles_list, get_categories_list,
                                                              GET_CATEGORIES_URL, DESCRIBE_PROFILES_URL,
                                                              describe_profiles, export_profiles,
                                                              EXPORT_PROFILES_URL, DIFF_PROFILES_URL, diff_profiles)
from testslib import unit_test_utils


class ProfileManagerAdaptorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.argument_dict = {"name": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30", "pid": "1234",
                              "num_nodes": 0, "schedule": "Every hour", "priority": "1", "last_run": "NEVER",
                              "user_count": 0}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.nodemanager_adaptor.service_adaptor.send_request_to_service')
    def test_send_request_to_service__success(self, mock_send_request):

        send_request_to_service(POST_METHOD, SET_STATUS_URL, self.argument_dict)
        mock_send_request.assert_called_with(POST_METHOD, SET_STATUS_URL, SERVICE_NAME, json_data=self.argument_dict,
                                             retry=True)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.can_service_be_used', return_value=True)
    def test_can_service_be_used__is_sucessful_for_profile(self, mock_can_service_be_used):
        profile = Mock()
        self.assertTrue(can_service_be_used(profile))
        mock_can_service_be_used.assert_called_with("profilemanager", profile)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.can_service_be_used', return_value=True)
    def test_can_service_be_used__is_sucessful_for_tools(self, mock_can_service_be_used):
        self.assertTrue(can_service_be_used())
        mock_can_service_be_used.assert_called_with("profilemanager", None)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_set_status__success(self, mock_send):
        set_status(self.argument_dict)
        mock_send.assert_called_with(POST_METHOD, SET_STATUS_URL, SERVICE_NAME, json_data=self.argument_dict,
                                     retry=True)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_add_profile_exception__success(self, mock_send):
        argument_dict = {"profile_key": "TEST_00-warnings", "profile_values": {"Error": "error"}}
        add_profile_exception(argument_dict)
        mock_send.assert_called_with(POST_METHOD, ADD_EXCEPTION_URL, SERVICE_NAME, json_data=argument_dict, retry=True)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.timestamp.convert_str_to_datetime_object')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_get_status__success(self, mock_send, _):
        argument_dict = {"profiles_list": None, "category": None}
        mock_send.return_value.json.return_value = [{"NAME": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30",
                                                     "pid": "1234", "num_nodes": 0, "schedule": "Every hour",
                                                     "priority": "1", "last_run": "NEVER", "user_count": 0},
                                                    {"NAME": "TEST_01", "state": "OK", "start_time": "None",
                                                     "pid": "1234", "num_nodes": 0, "schedule": "Every hour",
                                                     "priority": "M", "last_run": "2020-01-32 10:30", "user_count": 0},
                                                    {'NAME': 'CMEVENTS_NBI_01',
                                                     'schedule': 'Every 0:01:00 (last run: 19-May 16:58:16, '
                                                                 'next run: 19-May 16:59:16)',
                                                     'start_time': "2019-06-13 10:13:43",
                                                     'pid': 61665,
                                                     'last_run': "2020-05-19 16:58:16",
                                                     'num_nodes': 0, 'priority': 2, 'state': 'SLEEPING'}]

        get_status(argument_dict)
        mock_send.assert_called_with(POST_METHOD, GET_STATUS_URL, SERVICE_NAME,
                                     json_data={"profiles": "None", "category": "None"}, retry=True)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.timestamp.convert_str_to_datetime_object')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_get_status__if_json_response_is_true(self, mock_send, _):
        argument_dict = {"profiles_list": None, "category": None, "json_response": True}
        mock_send.return_value.json.return_value = [{"NAME": "TEST_00", "state": "OK", "start_time": "2020-01-32 10:30",
                                                     "pid": "1234", "num_nodes": 0, "schedule": "Every hour",
                                                     "priority": "1", "last_run": "NEVER", "user_count": 0},
                                                    {"NAME": "TEST_01", "state": "OK", "start_time": "None",
                                                     "pid": "1234", "num_nodes": 0, "schedule": "Every hour",
                                                     "priority": "M", "last_run": "2020-01-32 10:30", "user_count": 0},
                                                    {'NAME': 'CMEVENTS_NBI_01',
                                                     'schedule': 'Every 0:01:00 (last run: 19-May 16:58:16, '
                                                                 'next run: 19-May 16:59:16)',
                                                     'start_time': "2019-06-13 10:13:43",
                                                     'pid': 61665,
                                                     'last_run': "2020-05-19 16:58:16",
                                                     'num_nodes': 0, 'priority': 2, 'state': 'SLEEPING'}]

        get_status(argument_dict)
        mock_send.assert_called_with(POST_METHOD, GET_STATUS_URL, SERVICE_NAME,
                                     json_data={"profiles": "None", "category": "None"}, retry=True)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_clear_profile_pid_files__logs_message_if_success(self, mock_send, mock_print):
        response = Mock()
        response.ok = True
        response.json.return_value = {"status_code": 200, "message": "message"}
        mock_send.return_value = response
        clear_profile_pid_files(["AP_11"])
        mock_send.assert_called_with(POST_METHOD, CLEAR_PIDS_URL, SERVICE_NAME, json_data={"profile_names": ["AP_11"]},
                                     retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_clear_profile_exceptions__logs_message_if_success(self, mock_send, mock_print):
        clear_profile_exceptions()
        mock_send.assert_called_with(POST_METHOD, CLEAR_ERRORS_URL, SERVICE_NAME, json_data={"profile_names": "None"},
                                     retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_get_all_profiles_list__success(self, mock_send, mock_print):
        get_all_profiles_list()
        mock_send.assert_called_with(POST_METHOD, GET_PROFILES_URL, SERVICE_NAME, json_data=None, retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_get_all_categories_list__success(self, mock_send, mock_print):
        get_categories_list()
        mock_send.assert_called_with(POST_METHOD, GET_CATEGORIES_URL, SERVICE_NAME, json_data=None, retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_describe_profiles__success(self, mock_send, mock_print):
        describe_profiles(["TEST_00", "TEST_01"])
        mock_send.assert_called_with(POST_METHOD, DESCRIBE_PROFILES_URL, SERVICE_NAME,
                                     json_data={"profile_names": ["TEST_00", "TEST_01"]}, retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch('enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message')
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_export_profiles__success(self, mock_send, mock_print):
        args = {
            "profiles_to_export": ["TEST_00"],
            "export_file_path": "path",
            "categories_to_export": "None",
            "all_profiles": "None",
            "all_categories": True
        }
        export_profiles(["TEST_00"], "path", all_categories=True)
        mock_send.assert_called_with(POST_METHOD, EXPORT_PROFILES_URL, SERVICE_NAME,
                                     json_data=args, retry=False)
        self.assertEqual(1, mock_print.call_count)

    @patch("enmutils_int.lib.services.profilemanager_adaptor.print_service_operation_message")
    @patch('enmutils_int.lib.services.profilemanager_adaptor.service_adaptor.send_request_to_service')
    def test_diff_profiles__is_successful(self, mock_send, mock_print):
        parameters = {"blah": "di-blah"}
        diff_profiles(**parameters)
        mock_send.assert_called_with(POST_METHOD, DIFF_PROFILES_URL, SERVICE_NAME,
                                     json_data={"diff_parameters": parameters}, retry=False)
        self.assertEqual(1, mock_print.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
