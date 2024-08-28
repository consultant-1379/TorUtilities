#!/usr/bin/env python
import unittest2
from flask import Flask
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError

import enmutils_int.lib.services.usermanager as usermanager
import enmutils_int.lib.services.usermanager_helper_methods as helper
from enmutils.lib import log
from testslib import unit_test_utils

app = Flask(__name__)
LOG_DIR = '/home/enmutils/services'
SUCCESS_MSG_TRUE = '{"message": "", "success": true}'
CONTENT_TYPE = {'ContentType': 'application/json'}
CREATE_URI = '/create'
SESSIONS_INFO_URI = '/sessions'
DELETE_FUNCTION_STR = "Function: [{0}] with args: {1}."
MESSAGE = "Could not create user(s) on ENM due to :: Some Error."


class UserManagerServiceUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.usermanager.create_and_start_background_scheduled_job')
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.helper.'
           'fetch_and_set_enm_url_from_deploymentinfomanager')
    def test_at_startup__creates_backgroud_job(self, mock_fetch_url, mock_logger, mock_background):
        usermanager.at_startup()
        mock_background.assert_called_with(mock_fetch_url, 1440, 'usermanager_DAILY', mock_logger)
        mock_logger.debug.assert_any_call("Running startup function")
        mock_logger.debug.assert_any_call("Startup complete")

    @patch("enmutils_int.lib.services.usermanager.execute_create_flow",
           return_value=([{"username": 'test', "password": 'test', "keep_password": 'test',
                           "persist": 'test', "_session_key": 'test'}], []))
    @patch('enmutils_int.lib.services.usermanager.CustomContainsQueue.block_until_item_removed')
    @patch("enmutils_int.lib.services.usermanager.user_count_threshold_abort_check")
    @patch("enmutils_int.lib.services.usermanager.helper.create_user_role_objects")
    @patch("enmutils_int.lib.services.usermanager.helper.generate_user_info_list", return_value=[{'test_user': 'test'}])
    def test_create__is_successful_if_users_can_be_created(self, mock_generate_users_list, mock_create_roles, *_):
        with app.test_client() as client:
            client.post(CREATE_URI, json=dict(username_prefix="PM_XX", number_of_users=1,
                                              user_roles=["role1", "role2"]))
            usermanager.create()
        mock_generate_users_list.assert_called_with([{'username': 'test', 'keep_password': 'test', 'password': 'test',
                                                      '_session_key': 'test', 'persist': 'test'}])
        mock_create_roles.assert_called_once_with(["role1", "role2"])

    @patch("enmutils_int.lib.services.usermanager.user_count_threshold_abort_check")
    @patch("enmutils_int.lib.services.usermanager.helper.create_user_role_objects")
    @patch("enmutils_int.lib.services.usermanager.execute_create_flow", side_effect=Exception("Some Error"))
    @patch('enmutils_int.lib.services.usermanager.CustomContainsQueue.block_until_item_removed')
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.abort_with_message')
    def test_create__is_failed_if_enm_error(self, mock_abort, mock_logger, *_):
        with app.test_client() as client:
            client.post(CREATE_URI, json=dict(username_prefix="PM_XX", number_of_users=1,
                                              user_roles=["role1", "role2"]))
            usermanager.create()
        mock_abort.assert_called_with(MESSAGE, mock_logger, usermanager.SERVICE_NAME, LOG_DIR, http_status_code=500)

    @patch("enmutils_int.lib.services.usermanager.user_count_threshold_abort_check")
    @patch('enmutils_int.lib.services.usermanager.CustomContainsQueue.block_until_item_removed')
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.abort_with_message')
    def test_create__is_failed_if_missing_manditory_data_in_request(self, mock_abort, mock_logger, mock_block, *_):
        with app.test_client() as client:
            client.post(CREATE_URI, json=dict(username_prefix="PM_XX", number_of_users=1))
            usermanager.create()
            message = "Bad request. username_prefix: PM_XX, number_of_users (int): 1, user_roles (list): None"
            mock_abort.assert_called_with(message, mock_logger, usermanager.SERVICE_NAME, LOG_DIR, http_status_code=400)
            mock_block.assert_called_with("PM_XX", mock_logger)

    @patch('enmutils_int.lib.services.usermanager.helper.check_user_count_threshold',
           return_value=('test', 409))
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.abort_with_message')
    def test_user_count_threshold_abort_check__success(self, mock_abort, mock_logger, _):
        usermanager.user_count_threshold_abort_check()
        mock_abort.assert_called_with('test', mock_logger, usermanager.SERVICE_NAME, LOG_DIR, http_status_code=409)

    @patch('enmutils_int.lib.services.usermanager.helper.check_user_count_threshold',
           return_value=None)
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.abort_with_message')
    def test_user_count_threshold_abort_check__does_not_abort(self, mock_abort, mock_logger, _):
        usermanager.user_count_threshold_abort_check()
        self.assertEqual(0, mock_abort.call_count)
        self.assertEqual(0, mock_logger.call_count)

    @patch("enmutils_int.lib.services.usermanager.get_users_info")
    @patch("enmutils_int.lib.services.usermanager.helper.delete_existing_users")
    @patch("enmutils_int.lib.services.usermanager.create_users_operation")
    def test_execute_create_flow__is_successful(self, mock_create, mock_delete_users, mock_get_users):
        users = [Mock(roles=[Mock(name="Role")]), Mock(roles=[Mock(name="Role1")])]
        expected = mock_create.return_value = (users, [])
        result = usermanager.execute_create_flow("XXX", 1, ["ADMIN"], 'test_profile')
        self.assertEqual(result, expected)
        mock_delete_users.assert_called_once_with('test_profile', ['ADMIN'])
        mock_get_users.assert_called_once_with('', 'test_profile', '')

    @patch("enmutils_int.lib.services.usermanager.log.logger.debug")
    @patch("enmutils_int.lib.services.usermanager.helper.delete_existing_users", side_effect=Exception("ENM problem"))
    def test_execute_create_flow__raises_runtimeerror_if_cannot_create_users(self, *_):
        with self.assertRaises(RuntimeError) as error:
            usermanager.execute_create_flow("XXX", 1, ["ADMIN"], 'test_profile')
        self.assertEqual(error.exception.message, "Error in execute_create_flow: ENM problem")

    @patch('json.dumps')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list')
    def test_enm_users_route(self, mock_enm_users, _):
        usermanager.enm_users()
        self.assertEqual(mock_enm_users.call_count, 1)

    @patch('enmutils_int.lib.services.usermanager.abort')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list')
    def test_enm_users_route__reuses_status_code(self, mock_enm_users, mock_abort):
        response = Mock()
        response.status_code = 500
        mock_enm_users.side_effect = HTTPError(response=response)
        usermanager.enm_users()
        mock_abort.assert_called_with(500)
        self.assertEqual(mock_enm_users.call_count, 1)

    @patch('enmutils_int.lib.services.usermanager.abort')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list')
    def test_enm_users_route__defaults_to_404(self, mock_enm_users, mock_abort):
        mock_enm_users.side_effect = Exception("Error")
        usermanager.enm_users()
        mock_abort.assert_called_with(404)
        self.assertEqual(mock_enm_users.call_count, 1)

    @patch('json.dumps')
    @patch('enmutils_int.lib.services.usermanager.get_users_info')
    def test_get_users__route_is_successful_if_no_parameters_included_in_request(self, mock_get_users_info, _):
        with app.test_request_context():
            usermanager.get_users()
        mock_get_users_info.assert_called_with(None, None, None)

    @patch('json.dumps')
    @patch('enmutils_int.lib.services.usermanager.get_users_info')
    def test_get_users__route_is_successful_if_username_included_in_request(self, mock_get_users_info, _):
        with app.test_request_context('/users?username=Test_01_000'):
            usermanager.get_users()
        mock_get_users_info.assert_called_with("Test_01_000", None, None)

    @patch('json.dumps')
    @patch('enmutils_int.lib.services.usermanager.get_users_info')
    def test_get_users__route_is_successful_if_profile_and_user_roles_included_in_request(
            self, mock_get_users_info, mock_dumps):
        with app.test_request_context('/users?profile=Test_01&user_roles=Cmedit_Operator'):
            usermanager.get_users()
        mock_get_users_info.assert_called_with(None, "Test_01", "Cmedit_Operator")
        mock_dumps.assert_called_with(mock_get_users_info.return_value)

    @patch("enmutils_int.lib.services.usermanager.helper.get_enm_users_list", return_value=[])
    @patch("enmutils_int.lib.services.usermanager.persistence.get")
    def test_get_users_info__is_successful_if_username_specified(self, mock_get, _):
        expected = [{
            "username": "blah1", "password": "blah1", "persist": True, "_session_key": "key", "keep_password": True}]
        user1 = Mock(username="blah1", password="blah1", persist=True, _session_key="key", keep_password=True)

        mock_get.return_value = user1
        self.assertListEqual(expected, usermanager.get_users_info("TEST_01_1234_567890", "", ""))

    @patch("enmutils_int.lib.services.usermanager.helper.get_enm_users_list",
           return_value=["TEST_01_01", "TEST_01_02", "admin"])
    @patch("enmutils_int.lib.services.usermanager.persistence.get_all_default_keys",
           return_value=["TEST_01_01_session", "TEST_01_02_session", "TEST_01_03_session", "admin_session"])
    @patch("enmutils_int.lib.services.usermanager.persistence.remove")
    @patch("enmutils_int.lib.services.usermanager.persistence.get")
    def test_get_users_info__is_successful_if_profile_name_specified(self, mock_get, mock_remove, *_):
        expected = [{"username": "TEST_01_01", "password": "blah1", "persist": True, "_session_key": "key",
                     "keep_password": True},
                    {"username": "TEST_01_02", "password": "blah2", "persist": True, "_session_key": "key",
                     "keep_password": True}]
        user1 = Mock(password="blah1", persist=True, _session_key="key", keep_password=True)
        user1.username = "TEST_01_01"
        user2 = Mock(password="blah2", persist=True, _session_key="key", keep_password=True)
        user2.username = "TEST_01_02"
        user3 = Mock(password="blah3", persist=True, _session_key="key", keep_password=True)
        user3.username = "TEST_01_03"

        mock_get.side_effect = [user1, user2, user3]
        self.assertEqual(expected, usermanager.get_users_info("", "TEST_01", ""))
        self.assertEqual(1, mock_remove.call_count)

    @patch("enmutils_int.lib.services.usermanager.helper.get_enm_users_list", side_effect=Exception("Error"))
    @patch("enmutils_int.lib.services.usermanager.persistence.get_all_default_keys",
           return_value=["TEST_01_01_session", "TEST_01_02_session", "admin_session"])
    @patch("enmutils_int.lib.services.usermanager.get_users_with_matching_user_roles")
    @patch("enmutils_int.lib.services.usermanager.persistence.get")
    def test_get_users_info__is_successful_if_profile_name_and_user_roles_specified(
            self, mock_get, mock_get_users_with_matching_user_roles, *_):
        expected = [{"username": "blah2", "password": "blah2", "persist": True, "_session_key": "key",
                     "keep_password": True}]
        user1 = Mock(username="blah1", password="blah1", persist=True, _session_key="key", keep_password=True)
        user2 = Mock(username="blah2", password="blah2", persist=True, _session_key="key", keep_password=True)

        mock_get.side_effect = [user1, user2]
        mock_get_users_with_matching_user_roles.return_value = [user2]

        self.assertEqual(expected, usermanager.get_users_info("", "TEST_01", "some_roles"))
        mock_get_users_with_matching_user_roles.assert_called_with([user1, user2], "some_roles")

    @patch("enmutils_int.lib.services.usermanager.helper.get_enm_users_list", return_value=[])
    @patch("enmutils_int.lib.services.usermanager.persistence.get_all_default_keys",
           return_value=["Blah2_session", "TEST_01_02_session"])
    @patch("enmutils_int.lib.services.usermanager.persistence.get")
    def test_get_users_info__is_successful_if_all_users_requested(self, mock_get, *_):
        expected = [{"username": "blah1", "password": "blah1", "persist": True, "_session_key": "key",
                     "keep_password": True},
                    {"username": "blah2", "password": "blah2", "persist": True, "_session_key": "key",
                     "keep_password": True}]
        user1 = Mock(username="blah1", password="blah1", persist=True, _session_key="key", keep_password=True)
        user2 = Mock(username="blah2", password="blah2", persist=True, _session_key="key", keep_password=True)

        mock_get.side_effect = [user1, user2]
        self.assertEqual(expected, usermanager.get_users_info("", "", ""))

    def test_get_users_with_matching_user_roles__is_successful(self):
        cmedit_operator_role = Mock()
        cmedit_operator_role.name = "Cmedit_Operator"
        cmedit_administrator_role = Mock()
        cmedit_administrator_role.name = "Cmedit_Administrator"

        enm_user1_username = "TEST_01_1234_56789"
        enm_user1_roles = [cmedit_operator_role]
        enm_user1 = Mock(username=enm_user1_username, roles=set(enm_user1_roles))

        enm_user2_username = "TEST_01_2345_67890"
        enm_user2_roles = [cmedit_operator_role, cmedit_administrator_role]
        enm_user2 = Mock(username=enm_user2_username, roles=set(enm_user2_roles))

        result = usermanager.get_users_with_matching_user_roles([enm_user1, enm_user2],
                                                                "Cmedit_Operator,Cmedit_Administrator")
        self.assertEqual(result, [enm_user2])

    @patch('enmutils_int.lib.services.usermanager.get_users_info', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.usermanager.abort')
    def test_get_users_route__all_404(self, mock_abort, _):
        with app.test_request_context():
            usermanager.get_users()
            mock_abort.assert_called_with(404)

    @patch('enmutils_int.lib.services.usermanager.log.logger.debug')
    @patch('enmutils_int.lib.services.usermanager.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list', return_value=["Test_02", "Test_01"])
    @patch('enmutils_int.lib.services.usermanager.enm_user_2.User.delete')
    def test_delete_user_from_enm_by_username__success(self, mock_delete, *_):
        username = "Test_01"
        usermanager.delete_user_from_enm_by_username(username)
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils_int.lib.services.usermanager.log.logger.debug')
    @patch('enmutils_int.lib.services.usermanager.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list', return_value=["Test_02", "Test_03"])
    @patch('enmutils_int.lib.services.usermanager.enm_user_2.User.delete')
    def test_delete_user_from_enm_by_username__no_user_match(self, mock_delete, *_):
        username = "Test_01"
        usermanager.delete_user_from_enm_by_username(username)
        self.assertEqual(0, mock_delete.call_count)

    @patch('enmutils_int.lib.services.usermanager.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.usermanager.enm_user_2.User.delete')
    @patch('enmutils_int.lib.services.usermanager.log.logger.debug')
    def test_delete_user_from_enm_by_username__logs_failure(self, mock_debug, mock_delete, *_):
        username = "Test_01"
        usermanager.delete_user_from_enm_by_username(username)
        mock_debug.assert_any_call("User not deleted from ENM, error encountered :: Error")
        self.assertEqual(0, mock_delete.call_count)

    @patch('enmutils_int.lib.services.usermanager.CustomContainsQueue.get_item')
    @patch('enmutils_int.lib.services.usermanager.delete_profile_users')
    def test_delete_profile_users_from_enm__calls_delete_profile_users(self, mock_delete, mock_get_item):
        profile = "Test"
        usermanager.delete_profile_users_from_enm(profile)
        mock_delete.assert_called_with(profile)
        mock_get_item.assert_called_with(profile)

    @patch('enmutils_int.lib.services.usermanager.workload_admin_with_hostname',
           return_value='workload_admin_host')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list',
           return_value=["administrator", "workload_admin_host"])
    @patch('enmutils_int.lib.services.usermanager.delete_user_from_enm_by_username')
    def test_delete_all_users_from_enm__ignores_admin_users(self, mock_delete, *_):
        self.assertTrue(usermanager.delete_all_users_from_enm())
        self.assertEqual(0, mock_delete.call_count)

    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_list',
           return_value=["Test", "Test_01", "Test_02"])
    @patch('enmutils_int.lib.services.usermanager.delete_user_from_enm_by_username',
           side_effect=[None, Exception(""), None])
    def test_delete_all_users_from_enm__failure(self, mock_delete, _):
        self.assertFalse(usermanager.delete_all_users_from_enm())
        self.assertEqual(3, mock_delete.call_count)

    @patch('enmutils_int.lib.services.usermanager.extract_delete_user_values', return_value=[None, "AP_11", ["ADMIN"]])
    @patch('enmutils_int.lib.services.usermanager.get_json_response',
           return_value=('{"message": "", "success": true}', 200, {'ContentType': 'application/json'}))
    @patch('enmutils_int.lib.services.usermanager.CustomContainsQueue.put_unique')
    @patch('enmutils_int.lib.services.usermanager.helper.get_enm_users_with_matching_user_roles',
           return_value=["user1", "user2"])
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.create_and_start_once_off_background_scheduled_job')
    def test_delete_users__delete_profile_users_success_if_roles(self, mock_create, mock_logger, *_):
        with app.test_request_context("/users/delete?delete_data=%7B'profile_name':%20'AP_11',%20'user_roles':%20'"
                                      "ADMINISTRATOR'%7D"):
            self.assertEqual(usermanager.delete_users(), (SUCCESS_MSG_TRUE, 200, CONTENT_TYPE))

            mock_create.assert_called_with(helper.delete_users_from_enm_by_usernames,
                                           DELETE_FUNCTION_STR.format('delete_users_from_enm_by_usernames',
                                                                      [['user1', 'user2']]),
                                           mock_logger, func_args=[['user1', 'user2']])

    @patch('enmutils_int.lib.services.usermanager.extract_delete_user_values', return_value=[None, "AP_11", None])
    @patch('enmutils_int.lib.services.usermanager.get_json_response',
           return_value=('{"message": "", "success": true}', 200, {'ContentType': 'application/json'}))
    @patch('enmutils_int.lib.services.usermanager.CustomContainsQueue.put_unique')
    @patch('enmutils_int.lib.services.usermanager.create_and_start_once_off_background_scheduled_job')
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    def test_delete_users__delete_all_profile_success(self, mock_logger, mock_create, mock_put, *_):
        with app.test_request_context("/users/delete?delete_data=%7B'profile_name':%20'AP_11'%7D"):
            self.assertEqual(usermanager.delete_users(), (SUCCESS_MSG_TRUE, 200, CONTENT_TYPE))
            mock_create.assert_called_with(usermanager.delete_profile_users_from_enm,
                                           DELETE_FUNCTION_STR.format('delete_profile_users_from_enm', ['AP_11']),
                                           mock_logger, func_args=['AP_11'])
            mock_put.assert_called_with("AP_11")

    @patch('enmutils_int.lib.services.usermanager.extract_delete_user_values', return_value=[None, None, None])
    @patch('enmutils_int.lib.services.usermanager.get_json_response',
           return_value=('{"message": "", "success": true}', 200, {'ContentType': 'application/json'}))
    @patch('enmutils_int.lib.services.usermanager.create_and_start_once_off_background_scheduled_job')
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    def test_delete_users__delete_all_success(self, mock_logger, mock_create, *_):
        with app.test_request_context('/users/delete'):
            self.assertEqual(usermanager.delete_users(), (SUCCESS_MSG_TRUE, 200, CONTENT_TYPE))
            mock_create.assert_called_with(usermanager.delete_all_users_from_enm,
                                           DELETE_FUNCTION_STR.format('delete_all_users_from_enm', None), mock_logger,
                                           func_args=None)

    @patch('enmutils_int.lib.services.usermanager.extract_delete_user_values', return_value=["User_01", None, None])
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.create_and_start_once_off_background_scheduled_job',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.usermanager.abort_with_message')
    def test_delete_users__exception(self, mock_abort_with_message, mock_create, mock_logger, *_):
        with app.test_request_context("/users/delete?delete_data=None"):
            usermanager.delete_users()
            mock_abort_with_message.assert_called_with("Could not delete user(s), error encountered :: Error.",
                                                       mock_logger, usermanager.SERVICE_NAME, log.SERVICES_LOG_DIR)
            mock_create.assert_called_with(
                usermanager.delete_user_from_enm_by_username,
                DELETE_FUNCTION_STR.format('delete_user_from_enm_by_username', ['User_01']),
                mock_logger, func_args=['User_01'])

    def test_extract_delete_user_values__returns_none_if_no_delete_data(self):
        delete_request = Mock(args={"METHOD": "DELETE"})
        username, profile_name, user_roles = usermanager.extract_delete_user_values(delete_request)
        self.assertTrue(not all([username, profile_name, user_roles]))

    def test_extract_delete_user_values__extracts_values_if_found(self):
        delete_request = Mock(args={
            "delete_data": "'username': 'User01', 'profile_name': 'AP_11', 'user_roles': 'ADMIN||OPERATOR||SYSADMIN'"})
        username, profile_name, user_roles = usermanager.extract_delete_user_values(delete_request)
        self.assertEqual(username, "User01")
        self.assertEqual(profile_name, "AP_11")
        self.assertListEqual(user_roles, ['ADMIN', 'OPERATOR', 'SYSADMIN'])

    @patch('enmutils_int.lib.services.usermanager.get_json_response',
           return_value=('{"message": "", "success": true}', 200, {'ContentType': 'application/json'}))
    @patch("enmutils_int.lib.services.usermanager.helper.get_sessions_info", return_value=({'test'}, 'test', ))
    def test_sessions_per_profile__success(self, *_):
        result = ('{"message": "", "success": true}', 200, CONTENT_TYPE)
        with app.test_client() as client:
            client.post(SESSIONS_INFO_URI, json=dict(profiles=['logviewer_01']))
            response = usermanager.sessions_per_profile()
        self.assertEqual(result, response)

    @patch("enmutils_int.lib.services.usermanager.helper.get_sessions_info", side_effect=Exception('some_error'))
    @patch('enmutils_int.lib.services.usermanager.log.logger')
    @patch('enmutils_int.lib.services.usermanager.abort_with_message')
    def test_sessions_per_profile__return_error_message(self, mock_abort_with_message, mock_logger, *_):
        with app.test_client() as client:
            client.post(SESSIONS_INFO_URI, json=dict(profiles=['logviewer_01']))
            usermanager.sessions_per_profile()
        mock_abort_with_message.assert_called_with('Could not get information about profile sessions :: some_error.',
                                                   mock_logger, 'usermanager',
                                                   '/home/enmutils/services')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
