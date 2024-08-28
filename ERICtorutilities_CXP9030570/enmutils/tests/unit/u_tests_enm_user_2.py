#!/usr/bin/env python
import unittest2

from mock import patch, Mock, mock_open, call, MagicMock

from enmutils.lib.enm_user_2 import (User, HTTPError, get_or_create_admin_user, get_user_key, get_admin_user,
                                     load_credentials_from_props_or_prompt_for_credentials, NoStoredPasswordError,
                                     create_the_user_instance_and_log_in_if_specified, SessionNotEstablishedException,
                                     SessionTimeoutException, NoOuputFromScriptEngineResponseError, RequestException,
                                     EnmApplicationError, RolesAssignmentError, PasswordDisableError, EnmRole,
                                     get_user_privileges, get_all_sessions, raise_for_status, _prompt_for_credentials,
                                     build_user_message, is_session_available, _get_failed_response, CustomRole,
                                     verify_credentials, AUTH_COOKIE_KEY, fetch_credentials_create_user_instance,
                                     check_haproxy_online, ConnectionError, Target, RoleCapability, EnmRoleAlias,
                                     EnmComRole, verify_json_response)
from enmutils.lib.exceptions import EnvironError
from testslib import unit_test_utils

HA_PROXY_ONLINE = "/opt/ericsson/enminst/bin/vcs.bsh --groups -g Grp_CS_svc_cluster_haproxy_ext | egrep -i online"


class EnmUserUnitTests2(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        # User created purely for init logic - use the next user for consistency
        self.user_with_name = User(username="TestUser", password="Password", first_name="First", last_name="Last")
        self.user = User(username="TestUser", password="Password")
        self.retry_msg = ("WARNING: Session lost on application side. Removing current session from persistence and "
                          "trying to re-establish the session.")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.User.create')
    def test__enter__calls_create(self, mock_create):
        self.user.__enter__()
        self.assertEqual(1, mock_create.call_count)

    @patch('enmutils.lib.enm_user_2.User.delete')
    def test__exit__calls_delete(self, mock_delete):
        self.user.__exit__(None, None, None)
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils.lib.enm_user_2.exception.process_exception')
    @patch('enmutils.lib.enm_user_2.User.delete')
    def test__exit__processes_exceptions(self, mock_delete, mock_process_exception):
        self.user_with_name.__exit__("Exc", "Error", "TraceBack")
        self.assertEqual(1, mock_delete.call_count)
        self.assertEqual(1, mock_process_exception.call_count)

    def test_has_role_name__returns_role_name(self):
        role, role1 = Mock(), Mock()
        role.name, role1.name = "OPERATOR", "ADMIN"
        self.user.roles = [role, role1]
        self.assertTrue(self.user.has_role_name("ADMIN"))
        self.assertFalse(self.user.has_role_name("SECURITY"))

    @patch('enmutils.lib.enm_user_2.User.get')
    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_enm_user_information__success(self, mock_get_admin, mock_get):
        mock_get_admin.return_value.session = Mock()
        response = Mock(ok=True, text="{\"username\": \"TestUser\"}")
        mock_get.return_value = response
        self.assertDictEqual({"username": "TestUser"}, self.user.get_enm_user_information())

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_enm_user_information__raises_runtime_error(self, mock_get_admin):
        mock_get_admin.return_value.session = None
        self.assertRaises(RuntimeError, self.user.get_enm_user_information)

    @patch('enmutils.lib.enm_user_2.User.get')
    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_enm_user_information__returns_none_if_response_not_ok(self, mock_get_admin, mock_get):
        mock_get_admin.return_value.session = Mock()
        response = Mock(ok=False)
        mock_get.return_value = response
        self.assertIsNone(self.user.get_enm_user_information())

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.get_enm_user_information', return_value=True)
    @patch('enmutils.lib.enm_user_2.User.remove_session')
    def test_is_session_established__success(self, mock_remove, *_):
        self.user.enm_session = Mock()
        self.assertTrue(self.user.is_session_established())
        self.assertEqual(0, mock_remove.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.get_enm_user_information', return_value=None)
    @patch('enmutils.lib.enm_user_2.User.remove_session')
    def test_is_session_established__failure(self, mock_remove, *_):
        self.assertFalse(self.user.is_session_established())
        self.assertEqual(0, mock_remove.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session', side_effect=HTTPError("Error"))
    def test_is_session_established__raises_session_not_established_exception(self, _):
        self.assertRaises(SessionNotEstablishedException, self.user.is_session_established)

    @patch('enmutils.lib.enm_user_2.User.open_session', side_effect=NoStoredPasswordError("Error"))
    @patch('enmutils.lib.enm_user_2.User.remove_session')
    def test_is_session_established__removes_session(self, mock_remove, _):
        self.user.is_session_established()
        self.assertEqual(1, mock_remove.call_count)

    @patch('enmutils.lib.enm_user_2.User.login')
    def test_open_session__success(self, mock_login):
        self.user._session_key = None
        self.user.open_session(url="url")
        self.assertEqual(1, mock_login.call_count)

    @patch('enmutils.lib.enm_user_2.User.login')
    def test_open_session__session_key(self, mock_login):
        self.user._session_key = "key"
        self.user.open_session(url="url")
        self.assertEqual(0, mock_login.call_count)

    @patch('enmutils.lib.enm_user_2.cache.get_apache_url')
    def test_open_session__raises_no_stored_password(self, _):
        self.user.keep_password = False
        self.assertRaises(NoStoredPasswordError, self.user.open_session, reestablish=True)

    @patch('enmutils.lib.enm_user_2.User.login')
    def test_open_session__reestablish_success(self, mock_login, ):
        self.user.keep_password = True
        self.user.open_session(reestablish=True, url="url")
        self.assertEqual(1, mock_login.call_count)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    def test_login__success(self, _):
        self.user.persist = False
        session = Mock()
        session.cookies = {"iPlanetDirectoryPro": "key"}
        self.user.login(session)
        self.assertEqual("key", self.user._session_key)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.pkgutil.get_loader', return_value=False)
    @patch('enmutils.lib.enm_user_2.persistence.set')
    def test_login__does_not_persist_if_no_internal_package(self, mock_set, *_):
        self.user.persist = True
        session = Mock()
        session.cookies = {"iPlanetDirectoryPro": "key"}
        self.user.login(session)
        self.assertEqual(0, mock_set.call_count)

    @patch('enmutils.lib.enm_user_2.mutexer.mutex')
    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.pkgutil.get_loader', return_value=True)
    @patch('enmutils.lib.enm_user_2.persistence.set')
    def test_login__persists_user(self, mock_set, *_):
        self.user.persist = True
        session = Mock()
        session.cookies = {"iPlanetDirectoryPro": "key"}
        self.user.login(session)
        self.assertEqual(1, mock_set.call_count)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    def test_login__raises_http_error(self, _):
        session = Mock()
        session.open_session.side_effect = HTTPError("Error")
        self.assertRaises(HTTPError, self.user.login, session)

    @patch('enmutils.lib.enm_user_2.mutexer.mutex')
    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.persistence.remove')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_login__logs_401_error_and_removes_persisted_key(self, mock_debug, mock_remove, *_):
        session = Mock()
        session.open_session.side_effect = HTTPError("401 unauthorised")
        self.assertRaises(HTTPError, self.user.login, session)
        mock_debug.assert_called_with("User not authorised, please ensure user is created correctly and expected "
                                      "credentials are valid.")
        self.assertEqual(1, mock_remove.call_count)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.enmscripting.open')
    def test_open_enmscripting_session__success(self, mock_scripting_open, _):
        self.user.open_enmscripting_session("url")
        self.assertEqual(1, mock_scripting_open.call_count)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.enmscripting.open', side_effect=ValueError("Invalid"))
    def test_open_enmscripting_session__raise_session_timeout_exception(self, mock_scripting_open, _):
        self.assertRaises(SessionTimeoutException, self.user.open_enmscripting_session, "url")
        self.assertEqual(1, mock_scripting_open.call_count)

    def test_get_username_of_admin_user__success(self):
        self.assertEqual("TestUser", self.user.get_username_of_admin_user())

    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_usernames__success(self, mock_get):
        response = Mock(ok=True)
        response.json.return_value = [{"username": "TesUser"}]
        mock_get.return_value = response
        self.user.get_usernames(self.user)
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.persistence.remove')
    def test_remove_session__success(self, mock_remove, mock_debug_log):
        self.user._persistence_key = "key"
        self.user.enm_session = Mock()
        self.user.remove_session()
        mock_remove.assert_called_with("key")
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.persistence.remove')
    def test_remove_session__if_user_session_is_none(self, mock_remove, mock_debug_log):
        self.user._persistence_key = "key"
        self.user.enm_session = None
        self.user.remove_session()
        mock_remove.assert_called_with("key")
        self.assertEqual(0, mock_debug_log.call_count)

    def test_enm_scripting_session_value__success(self):
        self.assertEqual(None, self.user.get_enmscripting_session())
        self.user._enmscripting_session = "session"
        self.assertEqual("session", self.user.get_enmscripting_session())

    @patch('enmutils.lib.enm_user_2.User.open_enmscripting_session')
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    def test_execute_cmd__success(self, mock_session, _):
        session = Mock()
        session.url.return_value = "url"
        terminal_session = Mock()
        terminal_session.terminal.return_value.execute.return_value = "Ok"
        self.user.enm_session = session
        mock_session.return_value = terminal_session
        self.assertEqual("Ok", self.user._execute_cmd("cmd", on_terminal=True, timeout=10))

    @patch('enmutils.lib.enm_user_2.User.open_enmscripting_session')
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    def test_execute_cmd__does_open_enmscripting_if_no_attribute(self, mock_session, mock_open_enmscripting):
        session = Mock()
        session.url.return_value = "url"
        terminal_session = Mock()
        terminal_session.terminal.return_value.execute.return_value = "Ok"
        delattr(self.user, "_enmscripting_session")
        self.user.enm_session = session
        mock_session.return_value = terminal_session
        self.assertEqual("Ok", self.user._execute_cmd("cmd_file", on_terminal=True, timeout=10))
        self.assertEqual(0, mock_open_enmscripting.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_enmscripting_session')
    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.enm_user_2.enmscripting.open')
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    def test_execute_cmd__raises_session_timeout(self, mock_session, *_):
        session = Mock()
        session.url.return_value = "url"
        command_session = Mock()
        command_session.command.return_value.execute.side_effect = SessionTimeoutException("Error")
        self.user.enm_session = session
        mock_session.return_value = command_session
        self.assertRaises(SessionTimeoutException, self.user._execute_cmd, "cmd", on_terminal=False)

    @patch('enmutils.lib.enm_user_2.User.open_enmscripting_session')
    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.enm_user_2.enmscripting.open')
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    def test_execute_cmd__raises_session_timeout_if_pool_is_closed(self, mock_session, *_):
        session = Mock()
        session.url.return_value = "url"
        command_session = Mock()
        command_session.command.return_value.execute.side_effect = Exception("Pool is closed")
        self.user.enm_session = session
        mock_session.return_value = command_session
        self.assertRaises(SessionTimeoutException, self.user._execute_cmd, "cmd", on_terminal=False)

    @patch('enmutils.lib.enm_user_2.User.open_enmscripting_session')
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    def test_execute_cmd__raises_exception(self, mock_session, _):
        session = Mock()
        session.url.return_value = "url"
        self.user.enm_session = session
        mock_session.side_effect = Exception("Error")
        self.assertRaises(Exception, self.user._execute_cmd, "cmd", on_terminal=False)

    @patch('enmutils.lib.enm_user_2.enmscripting.open')
    @patch('enmutils.lib.enm_user_2.User._close_file_and_close_session')
    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User._execute_cmd')
    def test_enm_execute__success(self, mock_execute_cmd, *_):
        response = Mock()
        response.is_command_result_available.return_value = True
        mock_execute_cmd.return_value = response
        self.assertEqual(response, self.user.enm_execute("cmd"))

    @patch('enmutils.lib.enm_user_2.enmscripting.open')
    @patch('enmutils.lib.enm_user_2.User._close_file_and_close_session')
    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User._execute_cmd')
    def test_enm_execute__downloads_file_if_available(self, mock_execute_cmd, *_):
        response, response_file = Mock(), Mock()
        response.is_command_result_available.return_value = True
        response.has_files.return_value = True
        response.files.return_value = [response_file]
        mock_execute_cmd.return_value = response
        self.assertEqual(response, self.user.enm_execute("cmd", outfile="file"))
        self.assertEqual(response_file.download.call_count, 1)

    @patch('os.path.isfile', return_value=False)
    @patch('enmutils.lib.enm_user_2.User.open_session')
    def test_enm_execute__raises_os_error(self, *_):
        self.assertRaises(OSError, self.user.enm_execute, "cmd", file_in="file")

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('os.path.isfile', return_value=True)
    @patch('enmutils.lib.enm_user_2.User._close_file_and_close_session')
    @patch('enmutils.lib.enm_user_2.User._execute_cmd')
    def test_enm_execute__raises_no_output_error(self, mock_execute_cmd, *_):
        session = Mock()
        session.url.return_value = "test"
        self.user.enm_session = session
        response = Mock()
        response.is_command_result_available.return_value = False
        mock_execute_cmd.return_value = response
        self.assertRaises(NoOuputFromScriptEngineResponseError, self.user.enm_execute, "password", timeout_seconds=60,
                          file_in="file")

    @patch('enmutils.lib.enm_user_2.enmscripting.open')
    @patch('enmutils.lib.enm_user_2.User._close_file_and_close_session')
    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User._execute_cmd', side_effect=Exception("Error"))
    def test_enm_execute__raises_enm_application_error(self, mock_execute_cmd, *_):
        response = Mock()
        response.is_command_result_available.return_value = True
        mock_execute_cmd.return_value = response
        self.assertRaises(EnmApplicationError, self.user.enm_execute, "cmd")

    @patch('enmutils.lib.enm_user_2.config.has_prop', return_value=True)
    @patch('enmutils.lib.enm_user_2.config.get_prop', return_value=True)
    def test_close_file_and_close_session__closes_file_object_if_supplied(self, *_):
        file_obj, session = Mock(), Mock()
        self.user.enm_session = session
        self.user._close_file_and_close_session(file_obj=file_obj)
        self.assertEqual(1, file_obj.close.call_count)

    @patch('enmutils.lib.enm_user_2.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.config.get_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    @patch('enmscripting.close')
    def test_close_file_and_close_session____only_uses_enmscripting_if_session(self, mock_scripting_close, *_):
        self.user.enm_session = "session"
        self.user._close_file_and_close_session(file_obj=None)
        self.assertEqual(1, mock_scripting_close.call_count)

    @patch('enmutils.lib.enm_user_2.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.config.get_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session', return_value=None)
    @patch('enmscripting.close')
    def test_close_file_and_close_session__does_not_use_enmscripting_if_no_session(self, mock_scripting_close, *_):
        self.user._close_file_and_close_session(file_obj=None)
        self.assertEqual(0, mock_scripting_close.call_count)

    @patch('enmutils.lib.enm_user_2.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.config.get_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.enmscripting.close')
    def test_close_file_and_close_session__closed_pool_error_while_closing_session(self, mock_scripting_close,
                                                                                   mock_debug, *_):
        self.user.enm_session = "session"
        mock_scripting_close.side_effect = Exception("Pool is closed")
        self.user._close_file_and_close_session(file_obj=None)
        self.assertEqual(1, mock_scripting_close.call_count)
        mock_debug.assert_called_with('The enm scripting session has already been closed for {0}'.format(self.user.username))

    @patch('enmutils.lib.enm_user_2.config.has_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.config.get_prop', return_value=False)
    @patch('enmutils.lib.enm_user_2.User.get_enmscripting_session')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.enmscripting.close')
    def test_close_file_and_close_session__error_while_closing_session(self, mock_scripting_close, mock_debug, *_):
        self.user.enm_session = "session"
        mock_scripting_close.side_effect = Exception("Some Error")
        self.user._close_file_and_close_session(file_obj=None)
        self.assertEqual(1, mock_scripting_close.call_count)
        mock_debug.assert_called_with("Some Error")

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_log_for_status__success(self, mock_debug):
        response = Mock()
        response.request.method = "GET"
        response.request.url = "url"
        self.user._log_for_status(response)
        mock_debug.assert_called_with('GET request to "url" was successful')

    @patch('enmutils.lib.enm_user_2.User._process_safe_request')
    def test_log_for_status__safe_request(self, mock_safe_request):
        response = Mock(status_code=200)
        response.request.method = "GET"
        response.request.url = "url"
        self.user.safe_request = True
        self.user._log_for_status(response)
        self.assertEqual(1, mock_safe_request.call_count)

    @patch('enmutils.lib.enm_user_2.persistence')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User._process_safe_request')
    def test_log_for_status__status_code_401_http_error(self, mock_safe_request, mock_debug, *_):
        response = Mock(status_code=401)
        response.text = "Error"
        response.request.method = "GET"
        response.url = "url"
        response.raise_for_status.side_effect = HTTPError(response=response)
        self.user.safe_request = True
        self.user._log_for_status(response)
        self.assertEqual(0, mock_safe_request.call_count)
        mock_debug.assert_called_with('GET request to "url" failed with status code 401. ENM session lost or failed to '
                                      'open.')

    @patch('enmutils.lib.enm_user_2.persistence')
    def test_netex_new_time__success(self, *_):
        self.user.netex_new_time('NETEX_03')

    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.User.netex_new_time')
    @patch('enmutils.lib.enm_user_2._get_failed_response')
    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request_response__Netex(self, *_):
        self.user.request_response(Mock(), 'url', 'NETEX_03', 'retry')

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User._process_safe_request')
    def test_log_for_status__http_error(self, mock_safe_request, mock_debug):
        response = Mock(status_code=504)
        response.text = "Error"
        response.request.method = "GET"
        response.url = "url"
        response.raise_for_status.side_effect = HTTPError(response=response)
        self.user.safe_request = True
        self.user._log_for_status(response)
        self.assertEqual(1, mock_safe_request.call_count)
        mock_debug.assert_called_with('GET request to "url" failed with status code 504 and response Error')

    def test_process_safe_request__failure(self):
        response = Mock(status_code=401, ok=False)
        response.text = "ERRORS"
        response.request.method = "GET"
        response.request.url = "http:/1"
        self.user.ui_response_info = {('GET', 'http:/<id>'): {False: 1, True: 0, "ERRORS": {500: "response"}}}
        self.user._process_safe_request(response)

    def test_process_safe_request__failure_matching_status_code(self):
        response = Mock(status_code=401, ok=False)
        response.text = "ERRORS"
        response.request.method = "GET"
        response.request.url = "http:/1"
        self.user.ui_response_info = {('GET', 'http:/<id>'): {False: 1, True: 0, "ERRORS": {401: "response"}}}
        self.user._process_safe_request(response)

    def test_process_safe_request__failure_no_existing_error(self):
        response = Mock(status_code=401, ok=False)
        response.text = "ERRORS"
        response.request.method = "GET"
        response.request.url = "http:/url"
        self.user.ui_response_info = {('GET', 'http:/url'): {False: 1, True: 0}}
        self.user._process_safe_request(response)

    def test_process_safe_request__success(self):
        response = Mock(status_code=200, ok=True)
        response.text = "Success"
        response.request.method = "GET"
        response.request.url = "http:/1.url"
        self.user._process_safe_request(response)

    @patch('enmutils.lib.enm_user_2.User._log_for_status')
    def test_make_request__success(self, mock_log):
        session = Mock()
        session.request.return_value = Mock()
        self.user.enm_session = session
        self.user._make_request("GET", "url")
        self.assertEqual(mock_log.call_count, 1)

    def test_make_request__raises_request_exception(self):
        session = Mock()
        session.get.side_effect = HTTPError(400)
        self.user.enm_session = session
        self.assertRaises(RequestException, self.user._make_request, "GET", "url", ignore_status_lst=[400])

    @patch('enmutils.lib.enm_user_2._get_failed_response')
    @patch('enmutils.lib.enm_user_2.User._log_for_status')
    def test_make_request__raises_request_exception_safe_request(self, mock_log, mock_get_response):
        session = Mock()
        session.get.return_value = None
        self.user.safe_request = True
        self.user.enm_session = session
        self.user._make_request("GET", "url")
        self.assertEqual(mock_log.call_count, 1)
        self.assertEqual(mock_get_response.call_count, 1)

    # request test cases
    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__success(self, mock_make_request, mock_parse, mock_validate_error_response, *_):
        parse_response = Mock(netloc=1)
        mock_parse.return_value = parse_response
        self.user.request("GET", "url")
        self.assertEqual(1, mock_make_request.call_count)
        self.assertEqual(0, mock_validate_error_response.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__raises_http_error(self, mock_make_request, mock_parse, mock_validate_error_response, *_):
        parse_response = Mock(netloc=1)
        mock_parse.return_value = parse_response
        response = Mock(status_code=500, text="Server error")
        mock_make_request.side_effect = HTTPError(response=response)
        mock_validate_error_response.side_effect = mock_make_request.side_effect
        self.assertRaises(HTTPError, self.user.request, "GET", "url")
        self.assertEqual(1, mock_make_request.call_count)
        self.assertEqual(1, mock_validate_error_response.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.build_user_message')
    @patch('enmutils.lib.enm_user_2.urljoin')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__retries_session_error(self, mock_make_request, mock_parse, mock_validate_error_response, *_):
        session = Mock()
        session.url.return_value = "url"
        parse_response = Mock(netloc=0)
        mock_parse.return_value = parse_response
        self.user.enm_session = session
        response = Mock(status_code=403)
        mock_make_request.side_effect = [HTTPError(response=response), None]
        self.user.request("GET", "url")
        self.assertEqual(2, mock_make_request.call_count)
        self.assertEqual(1, mock_validate_error_response.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.build_user_message')
    @patch('enmutils.lib.enm_user_2.urljoin')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__retries_session_response_failure_error(self, mock_make_request, mock_parse,
                                                             mock_validate_error_response, *_):
        session = Mock()
        session.url.return_value = "url"
        parse_response = Mock(netloc=0)
        mock_parse.return_value = parse_response
        self.user.enm_session = session
        response = Mock(status_code=403)
        mock_make_request.side_effect = [response, None]
        self.user.request("GET", "url")
        self.assertEqual(2, mock_make_request.call_count)
        self.assertEqual(0, mock_validate_error_response.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urljoin')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__updates_url_if_missing_forward_slash(self, mock_make_request, mock_parse, mock_join,
                                                           mock_validate_error_response, *_):
        parse_response = Mock(netloc=0)
        mock_parse.return_value = parse_response
        session = Mock()
        session.url.return_value = "http:://enm"
        self.user.enm_session = session
        self.user.request("GET", "url")
        self.assertEqual(0, mock_validate_error_response.call_count)
        self.assertEqual(1, mock_make_request.call_count)
        mock_join.assert_called_with('http:://enm', '/url')

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urljoin')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__does_not_update_url_if_forward_slash(self, mock_make_request, mock_parse, mock_join,
                                                           mock_validate_error_response, *_):
        parse_response = Mock(netloc=0)
        mock_parse.return_value = parse_response
        session = Mock()
        session.url.return_value = "http:://enm/"
        self.user.enm_session = session
        self.user.request("GET", "url")
        self.assertEqual(0, mock_validate_error_response.call_count)
        self.assertEqual(1, mock_make_request.call_count)
        mock_join.assert_called_with('http:://enm/', 'url')

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__retries_connection_error_if_network_is_unreachable(self, mock_make_request, mock_parse,
                                                                         mock_validate_error_response, *_):
        parse_response = Mock(netloc=1)
        mock_parse.return_value = parse_response
        mock_validate_error_response.return_value = True
        response = Mock(status_code=200, text="successful")
        connection_error = ConnectionError("Failed to make request, status code:: [503] Reason:: [Service Unavailable]")
        mock_make_request.side_effect = [connection_error, response]
        self.user.request("GET", "url")
        self.assertEqual(2, mock_make_request.call_count)
        mock_validate_error_response.assert_called_with(connection_error, self.retry_msg)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__retries_connection_error_if_service_unavailable(self, mock_make_request, mock_parse,
                                                                      mock_validate_error_response, *_):
        parse_response = Mock(netloc=1)
        mock_parse.return_value = parse_response
        mock_validate_error_response.return_value = True
        response = Mock(status_code=200, text="successful")
        connection_error = ConnectionError("Failed to make request, status code:: [503] Reason:: [Service Unavailable]")
        mock_make_request.side_effect = [connection_error, response]
        self.user.request("POST", "url")
        self.assertEqual(2, mock_make_request.call_count)
        mock_validate_error_response.assert_called_with(connection_error, self.retry_msg)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    @patch('enmutils.lib.enm_user_2.User.validate_error_response')
    @patch('enmutils.lib.enm_user_2.urlparse')
    @patch('enmutils.lib.enm_user_2.User._make_request')
    def test_request__validate_error_response_return_false(self, mock_make_request, mock_parse,
                                                           mock_validate_error_response, *_):
        parse_response = Mock(netloc=1)
        mock_parse.return_value = parse_response
        mock_validate_error_response.return_value = False
        response = Mock(status_code=200, text="successful")
        connection_error = ConnectionError("Failed to make request, status code:: [503] Reason:: [Service Unavailable]")
        mock_make_request.side_effect = [connection_error, response]
        self.user.request("GET", "url")
        self.assertEqual(1, mock_make_request.call_count)
        mock_validate_error_response.assert_called_with(connection_error, self.retry_msg)

    # validate_error_response test cases
    @patch('enmutils.lib.enm_user_2.check_haproxy_online', return_value=False)
    @patch('enmutils.lib.enm_user_2.time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.build_user_message')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_validate_error_response__retries_connection_error_if_service_unavailable(self, mock_debug_log, *_):
        connection_error = ConnectionError("Failed to make request, status code:: [503] Reason:: "
                                           "[Service Unavailable]")
        self.assertEqual(True, self.user.validate_error_response(connection_error, "retry_msg"))
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils.lib.enm_user_2.check_haproxy_online', return_value=False)
    @patch('enmutils.lib.enm_user_2.time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.build_user_message')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_validate_error_response__retries_connection_error_if_network_is_unreachable(self, mock_debug_log, *_):
        connection_error = ConnectionError("('Connection aborted.', error(101, 'Network is unreachable'))")
        self.assertEqual(True, self.user.validate_error_response(connection_error, "retry_msg"))
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils.lib.enm_user_2.check_haproxy_online', return_value=True)
    @patch('enmutils.lib.enm_user_2.time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.build_user_message')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_validate_error_response___retries_session_response_failure_error(self, mock_debug_log,
                                                                              mock_build_user_message, *_):
        response = Mock(status_code=403)
        self.assertEqual(True, self.user.validate_error_response(HTTPError(response=response), "retry_msg"))
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertTrue(mock_build_user_message.called)

    @patch('enmutils.lib.enm_user_2.check_haproxy_online', return_value=True)
    @patch('enmutils.lib.enm_user_2.time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.build_user_message')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_validate_error_response___raises_http_error(self, mock_debug_log, *_):
        response = Mock(status_code=500, text="Server error")
        self.assertRaises(HTTPError, self.user.validate_error_response, HTTPError(response=response), "retry_msg")
        self.assertEqual(mock_debug_log.call_count, 1)

    # get test cases
    @patch('enmutils.lib.enm_user_2.User.request')
    def test_get__calls_request(self, mock_request):
        self.user.get("url")
        self.assertEqual(mock_request.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.request')
    def test_head__calls_request(self, mock_request):
        self.user.head("url")
        self.assertEqual(mock_request.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.request')
    def test_post__calls_request(self, mock_request):
        self.user.post("url")
        self.assertEqual(mock_request.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.request')
    def test_put__calls_request(self, mock_request):
        self.user.put("url")
        self.assertEqual(mock_request.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.request')
    def test_delete_request__calls_request(self, mock_request):
        self.user.delete_request("url")
        self.assertEqual(mock_request.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.request')
    def test_patch__calls_request(self, mock_request):
        self.user.patch("url")
        self.assertEqual(mock_request.call_count, 1)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.User.establish_enm_session')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create__success(self, mock_post, mock_establish, *_):
        role, target = Mock(name="ADMIN"), Mock(name="ALL")
        role.targets = [target]
        self.user.roles = [role]
        response = Mock(status_code=200)
        mock_post.return_value = response
        self.user.create(create_as=self.user)
        self.assertEqual(1, mock_establish.call_count)

    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create__success_no_establish_session(self, mock_post, *_):
        role, target = Mock(name="ADMIN"), Mock(name="ALL")
        role.targets = [target]
        self.user.roles = [role]
        self.user.establish_session = False
        self.user.password_reset_disabled = False
        response = Mock(status_code=200)
        mock_post.return_value = response
        self.user.create(create_as=self.user)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.User.establish_enm_session')
    @patch('enmutils.lib.enm_user_2.User.get_http_error_for_failed_user_creation')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create_calls_get_http_response_for_failed_user_creation_successful(self, mock_post, mock_get_http_error,
                                                                                *_):
        role, target = Mock(name="ADMIN"), Mock(name="ALL")
        role.targets = [target]
        self.user.roles = [role]
        response = Mock(status_code=500)
        mock_post.return_value = response
        self.user.create(create_as=self.user)
        self.assertEqual(mock_get_http_error.call_count, 1)

    @patch('enmutils.lib.enm_user_2.build_user_message', return_value="User Profile workload_admin already exists")
    def test_get_http_error_for_failed_user_creation_raises_http_error_for_workload_admin_user(self, *_):
        response = "response"
        with self.assertRaises(HTTPError) as error:
            self.user.get_http_error_for_failed_user_creation(response)
        self.assertEqual(error.exception.message, "An attempt to create the user \"TestUser\" "
                                                  "has failed as that user already exists on ENM. "
                                                  "This is an unexpected situation."
                                                  "This user needs to be manually deleted from ENM "
                                                  "first before workload profiles can be started.")

    @patch('enmutils.lib.enm_user_2.build_user_message', return_value="User Profile failed already exists")
    def test_get_http_error_for_failed_user_creation_raises_http_error(self, *_):
        response = "response"
        with self.assertRaises(HTTPError) as error:
            self.user.get_http_error_for_failed_user_creation(response)
        self.assertEqual(error.exception.message, "User \"TestUser\" with 0 roles failed to create. "
                                                  "Reason \"User Profile failed already exists\"")

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.User.establish_enm_session', side_effect=HTTPError("Error"))
    @patch('enmutils.lib.enm_user_2.User.delete')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create__raises_run_time_error_establish_session(self, mock_post, mock_delete, *_):
        role, target = Mock(name="ADMIN"), Mock(name="ALL")
        role.targets = [target]
        self.user.roles = [role]
        response = Mock(status_code=200)
        mock_post.return_value = response
        self.assertRaises(RuntimeError, self.user.create, create_as=self.user)
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.User.establish_enm_session')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create__raises_enm_application_error(self, mock_post, *_):
        role, target = Mock(name="ADMIN"), Mock(name="ALL")
        role.targets = [target]
        self.user.roles = [role]
        mock_post.side_effect = Exception("Error")
        self.assertRaises(EnmApplicationError, self.user.create, create_as=self.user)

    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.config.get_encoded_password_and_decode', return_value="pass")
    @patch('enmutils.lib.enm_user_2.verify_credentials', return_value=None)
    @patch('enmutils.lib.enm_user_2.User.delete')
    @patch('enmutils.lib.enm_user_2.User.post')
    def test_create__raises_run_time_error(self, mock_post, mock_delete, *_):
        role, target = Mock(name="ADMIN"), Mock(name="ALL")
        role.targets = [target]
        self.user.roles = [role]
        session = Mock()
        session.url.return_value = "url"
        self.user.enm_session = session
        self.user.establish_session = False
        self.user.password_reset_disabled = True
        response = Mock(status_code=200)
        mock_post.return_value = response
        self.assertRaises(RuntimeError, self.user.create, create_as=self.user)
        self.assertEqual(0, mock_delete.call_count)

    @patch('enmutils.lib.enm_user_2.User.open_session')
    def test_establish_enm_session__success(self, _):
        self.assertTrue(self.user.establish_enm_session())

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.enm_user_2.User.open_session', side_effect=HTTPError())
    def test_establish_enm_session__raises_http_error(self, *_):
        self.assertRaises(HTTPError, self.user.establish_enm_session)

    @patch('enmutils.lib.enm_user_2.User.remove_session')
    @patch('enmutils.lib.enm_user_2.User.delete_request')
    def test_delete__success(self, mock_delete, mock_remove):
        response = Mock(status_code=200)
        mock_delete.return_value = response
        self.user.enm_session = "session"
        self.user.delete(delete_as=self.user)
        self.assertEqual(1, mock_remove.call_count)

    @patch('enmutils.lib.enm_user_2.User.remove_session')
    @patch('enmutils.lib.enm_user_2.User.delete_request')
    def test_delete__raises_http_error(self, mock_delete, mock_remove):
        response = Mock(status_code=302)
        mock_delete.return_value = response
        self.user.enm_session = "session"
        self.assertRaises(HTTPError, self.user.delete, delete_as=self.user)
        self.assertEqual(0, mock_remove.call_count)

    @patch('enmutils.lib.enm_user_2.persistence.remove')
    @patch('enmutils.lib.enm_user_2.User.delete_request')
    def test_delete__value_error(self, mock_delete, mock_remove):
        mock_delete.side_effect = ValueError("error")
        self.user.delete(delete_as=self.user)
        self.assertEqual(1, mock_remove.call_count)

    @patch('enmutils.lib.log.purple_text')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.put')
    def test_assign_to_roles__success(self, mock_put, mock_debug, _):
        response = Mock(status_code=200)
        role = Mock()
        role.name = "ADMIN"
        mock_put.return_value = response
        self.user.assign_to_roles(roles=[role], assign_as=self.user)
        mock_debug.assert_called_with('Successfully assigned roles "ADMIN" to user "TestUser"')

    @patch('enmutils.lib.log.purple_text')
    @patch('enmutils.lib.enm_user_2.User.put')
    def test_assign_to_roles__raises_role_assignment_error(self, mock_put, _):
        response = Mock(status_code=500, text="error")
        role = Mock()
        role.name = "ADMIN"
        mock_put.return_value = response
        self.assertRaises(RolesAssignmentError, self.user.assign_to_roles, roles=[role], assign_as=self.user)

    @patch('enmutils.lib.log.purple_text')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.User.put')
    def test_set_status__success(self, mock_put, mock_debug, _):
        response = Mock(status_code=200)
        mock_put.return_value = response
        self.user.set_status("disabled", assign_as=self.user)
        mock_debug.assert_called_with('Successfully changed status of user "TestUser" to "disabled"')

    @patch('enmutils.lib.log.purple_text')
    @patch('enmutils.lib.enm_user_2.User.put')
    def test_set_status__raises_http_error(self, mock_put, _):
        response = Mock(status_code=500, text="error")
        mock_put.return_value = response
        self.assertRaises(HTTPError, self.user.set_status, "disabled", assign_as=self.user)

    @patch('enmutils.lib.enm_user_2.User.delete')
    def test_teardown__calls_delete(self, mock_delete):
        self.user._teardown()
        self.assertEqual(1, mock_delete.call_count)

    @patch('enmutils.lib.enm_user_2.User.put')
    def test_change_password__success(self, mock_put):
        response = Mock(status_code=204)
        mock_put.return_value = response
        self.user.change_password(change_as=self.user)

    @patch('enmutils.lib.enm_user_2.User.put')
    def test_set_status__raises_password_disable_error(self, mock_put):
        response = Mock(status_code=500, text="error")
        mock_put.return_value = response
        self.assertRaises(PasswordDisableError, self.user.change_password, change_as=self.user)

    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_roles__success(self, mock_get):
        response = Mock(ok=True)
        response.json.return_value = [{"role": "ADMIN", "targetGroup": "ALL"}]
        mock_get.return_value = response
        for _ in self.user.get_roles():
            self.assertTrue(isinstance(_, EnmRole))

    @patch('enmutils.lib.enm_user_2.User.get')
    def test_get_roles__raises_http_error(self, mock_get):
        response = Mock(ok=False)
        mock_get.return_value = response
        self.assertRaises(HTTPError, self.user.get_roles)

    def test__set_state__resets_session(self):
        self.user.enm_session = "session"
        self.assertIsNotNone(self.user.session)
        self.user.__setstate__({"enm_session": "session1"})
        self.assertIsNone(self.user.session)


class EnmUserUnitTests2Credentials(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.filesystem.does_file_exist', return_value=True)
    @patch('enmutils.lib.enm_user_2.create_the_user_instance_and_log_in_if_specified')
    @patch('enmutils.lib.enm_user_2.filesystem.get_lines_from_file', return_value=["user", "pass"])
    def test_fetch_credentials_create_user_instance__reads_supplied_credentials(self, mock_get_lines, *_):
        fetch_credentials_create_user_instance("file", True)
        self.assertEqual(1, mock_get_lines.call_count)

    @patch('enmutils.lib.enm_user_2.filesystem.does_file_exist', return_value=False)
    @patch('enmutils.lib.enm_user_2.create_the_user_instance_and_log_in_if_specified')
    @patch('enmutils.lib.enm_user_2.load_credentials_from_props_or_prompt_for_credentials',
           return_value=[("user", "pass"), True])
    @patch('enmutils.lib.enm_user_2.filesystem.get_lines_from_file')
    def test_fetch_credentials_create_user_instance__loads_default_credentials(self, mock_get_lines, mock_load, *_):
        fetch_credentials_create_user_instance("file", True)
        self.assertEqual(0, mock_get_lines.call_count)
        self.assertEqual(1, mock_load.call_count)

    @patch('enmutils.lib.enm_user_2.filesystem.does_file_exist', return_value=True)
    @patch('enmutils.lib.enm_user_2.create_the_user_instance_and_log_in_if_specified')
    @patch('enmutils.lib.enm_user_2.filesystem.get_lines_from_file', return_value=[])
    def test_fetch_credentials_create_user_instance__raises_run_time_error(self, mock_get_lines, *_):
        self.assertRaises(RuntimeError, fetch_credentials_create_user_instance, "file", True)
        self.assertEqual(1, mock_get_lines.call_count)

    @patch('enmutils.lib.enm_user_2.User.get_username_of_admin_user', return_value='user')
    @patch('enmutils.lib.enm_user_2.User.open_session')
    def test_create_the_user_instance_and_log_in_if_specified_is_successful(self, mock_open_session, *_):
        test_credentials = ('user', 'pass')
        create_the_user_instance_and_log_in_if_specified(test_credentials)
        self.assertTrue(mock_open_session.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.open_session',
           side_effect=[Exception('Invalid login, credentials are invalid'), Mock()])
    @patch('enmutils.lib.enm_user_2.load_credentials_from_props_or_prompt_for_credentials')
    def test_create_the_user_instance_and_log_in_prompts_the_user_for_credentials_if_invalid_login(self,
                                                                                                   mock_load_creds, *_):
        test_credentials = ('user', 'pass')
        keep_password = False
        mock_load_creds.return_value = test_credentials, keep_password
        create_the_user_instance_and_log_in_if_specified(test_credentials)
        self.assertTrue(mock_load_creds.call_count, 1)

    @patch('enmutils.lib.enm_user_2.User.open_session', side_effect=Exception('Invalid login, credentials are invalid'))
    @patch('enmutils.lib.enm_user_2.load_credentials_from_props_or_prompt_for_credentials')
    def test_create_the_user_instance_and_log_in_prompts_the_user_for_credentials_doesnt_reprompt_if_max_credentials_prompt_is_reaches(
            self, mock_load_creds, _):
        test_credentials = ('user', 'pass')
        create_the_user_instance_and_log_in_if_specified(test_credentials, credentials_prompt=1)
        self.assertFalse(mock_load_creds.called)

    @patch('enmutils.lib.enm_user_2.User.open_session', side_effect=Exception('exception'))
    def test_create_the_user_instance_and_log_in_raises_exception(self, _):
        test_credentials = ('user', 'pass')
        self.assertRaises(Exception, create_the_user_instance_and_log_in_if_specified, test_credentials)

    @patch('enmutils.lib.enm_user_2.persistence.get', return_value=True)
    @patch('enmutils.lib.enm_user_2.User.open_session')
    def test_create_the_user_instance_and_log_in_if_specified_doesnt_open_session_when_specified(self,
                                                                                                 mock_open_session, *_):
        test_credentials = ('user', 'pass')
        create_the_user_instance_and_log_in_if_specified(test_credentials, open_session=False)
        self.assertFalse(mock_open_session.called)

    @patch('enmutils.lib.enm_user_2._prompt_for_credentials')
    @patch('enmutils.lib.enm_user_2.config.load_credentials_from_props')
    def test_load_credentials_from_props_or_prompt_for_credentials__prompts_when_no_credentials(self,
                                                                                                mock_load_credentials,
                                                                                                mock_prompt_for_creds,
                                                                                                *_):
        test_credentials = ()
        mock_load_credentials.return_value = test_credentials
        prompt_credentials = ('user', 'pass')
        mock_prompt_for_creds.return_value = prompt_credentials
        load_credentials_from_props_or_prompt_for_credentials("prompt", "user prompt", "pass_prompt")
        self.assertTrue(mock_prompt_for_creds.call_count, 1)

    @patch('enmutils.lib.enm_user_2._prompt_for_credentials')
    @patch('enmutils.lib.enm_user_2.config.load_credentials_from_props')
    def test_load_credentials_from_props_or_prompt_for_credentials_calls_prompt_for_creds_when_reprompt_true(self,
                                                                                                             mock_load_credentials,
                                                                                                             mock_prompt_for_creds,
                                                                                                             *_):
        load_credentials_from_props_or_prompt_for_credentials("prompt", "user prompt", "pass_prompt", reprompt=True)
        self.assertTrue(mock_prompt_for_creds.call_count, 1)
        self.assertFalse(mock_load_credentials.called)

    @patch('enmutils.lib.enm_user_2.config.load_credentials_from_props')
    def test_load_credentials_from_props_or_prompt_for_credentials_is_successful(self, mock_load_credentials, *_):
        test_credentials = ('user', 'pass')
        mock_load_credentials.return_value = test_credentials
        self.assertEqual(load_credentials_from_props_or_prompt_for_credentials("prompt", "user prompt", "pass_prompt"),
                         (test_credentials, True))

    @patch('enmutils.lib.enm_user_2.is_session_available', return_value=True)
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="User")
    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_get_admin_user_is_successful(self, mock_debug, mock_persistence_get, *_):
        get_admin_user()
        self.assertTrue(mock_persistence_get.called)
        mock_debug.assert_called_with("Getting the workload admin session")

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.is_session_available', return_value=False)
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="User")
    @patch('enmutils.lib.enm_user_2.persistence.get')
    def test_get_admin_user__raises_runtime_error_when_session_is_not_available(self, mock_persistence_get, *_):
        with self.assertRaises(RuntimeError):
            get_admin_user(retry=1)
        self.assertFalse(mock_persistence_get.called)

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.is_session_available', side_effect=[False, True])
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="User")
    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.fetch_credentials_create_user_instance')
    def test_get_admin_user__retries_before_raising_run_time_error(self, mock_fetch, *_):
        get_admin_user()
        self.assertEqual(1, mock_fetch.call_count)

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.is_session_available', side_effect=[False, False])
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="User")
    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.fetch_credentials_create_user_instance', side_effect=Exception)
    def test_get_admin_user__raises_run_time_error_if_create_fails(self, mock_fetch, *_):
        self.assertRaises(RuntimeError, get_admin_user)
        self.assertEqual(1, mock_fetch.call_count)

    @patch('enmutils.lib.enm_user_2.persistence.has_key', return_value=True)
    @patch('enmutils.lib.enm_user_2.cache.check_if_on_workload_vm', return_value=True)
    def test_get_user_key_is_successful(self, *_):
        self.assertEqual(get_user_key(), 'workload_admin_session')

    @patch('enmutils.lib.enm_user_2.persistence.has_key', return_value=False)
    @patch('enmutils.lib.enm_user_2.cache.check_if_on_workload_vm', return_value=True)
    def test_get_user_key_returns_default_admin_when_workload_admin_not_in_persistence(self, *_):
        self.assertEqual(get_user_key(), 'administrator_session')

    @patch('enmutils.lib.enm_user_2.cache.check_if_on_workload_vm', return_value=False)
    def test_get_user_key_returns_default_admin_when_users_internal_and_not_on_the_lms_returns_false(self, _):
        self.assertEqual(get_user_key(), 'administrator_session')

    @patch('enmutils.lib.enm_user_2.cache.check_if_on_workload_vm', return_value=True)
    def test_get_user_key_returns_default_admin_when_default_admin_flag_is_set_to_true(self, _):
        self.assertEqual(get_user_key(default_admin=True), 'administrator_session')

    @patch('enmutils.lib.enm_user_2.fetch_credentials_create_user_instance')
    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_or_create_admin_user__returns_workload_admin_user(self, mock_get_admin, mock_fetch):
        get_or_create_admin_user()
        self.assertEqual(mock_get_admin.call_count, 1)
        self.assertEqual(mock_fetch.call_count, 0)

    @patch('enmutils.lib.enm_user_2.fetch_credentials_create_user_instance')
    @patch('enmutils.lib.enm_user_2.get_admin_user', side_effect=RuntimeError)
    def test_get_or_create_admin_user__fetches_admin_user(self, mock_get_admin, mock_fetch):
        get_or_create_admin_user(enm_admin_creds_file="file")
        self.assertEqual(mock_get_admin.call_count, 1)
        self.assertEqual(mock_fetch.call_count, 1)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_user_privileges__success(self, _):
        response = Mock(ok=True)
        response.json.return_value = [{"role": "ADMIN", "targetGroup": "ALL"}]
        self.user.get.return_value = response
        get_response = get_user_privileges("User", self.user)
        for _ in get_response:
            self.assertTrue(isinstance(_, EnmRole))

    def test_get_user_privileges__raises_http_error(self):
        response = Mock(ok=False)
        self.user.get.return_value = response
        self.assertRaises(HTTPError, get_user_privileges, "User", self.user)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_all_sessions__success(self, mock_admin_user):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"User": 1, "User1": 1}
        mock_admin_user.return_value.get.return_value = response
        self.assertDictEqual(get_all_sessions(), {"User": 1, "User1": 1})

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_all_sessions__raises_http_error(self, mock_admin_user):
        response = Mock(text="Error")
        response.status_code = 500
        mock_admin_user.return_value.get.return_value = response
        self.assertRaises(HTTPError, get_all_sessions)

    @patch('time.sleep', return_value=0)
    @patch('enmutils.lib.enm_user_2.getpass.getpass', return_value="pass")
    @patch('__builtin__.raw_input')
    def test_prompt_for_credentials__success(self, mock_raw, *_):
        mock_raw.return_value = "user"
        self.assertEqual(("user", "pass"), _prompt_for_credentials("prompt", "prompt", "prompt"))

    @patch('enmutils.lib.enm_user_2.persistence.has_key', return_value=False)
    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="user")
    def test_is_session_available__gets_user_key(self, mock_get_user_key, mock_get_key, _):
        is_session_available("user")
        mock_get_user_key.assert_called_with("user")
        self.assertEqual(0, mock_get_key.call_count)

    @patch('enmutils.lib.enm_user_2.persistence.has_key', return_value=True)
    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="user")
    def test_is_session_available__check_session(self, mock_get_user_key, mock_get_key, _):
        user = Mock()
        user.is_session_established.return_value = False
        mock_get_key.return_value = user
        self.assertEqual(False, is_session_available("user", check_session=True))
        mock_get_user_key.assert_called_with("user")
        self.assertEqual(1, mock_get_key.call_count)

    @patch('enmutils.lib.enm_user_2.persistence.has_key', return_value=True)
    @patch('enmutils.lib.enm_user_2.persistence.get')
    @patch('enmutils.lib.enm_user_2.get_user_key', return_value="user")
    def test_is_session_available__no_session_check(self, mock_get_user_key, mock_get_key, _):
        user = Mock()
        mock_get_key.return_value = user
        self.assertEqual(True, is_session_available("user", check_session=False))
        mock_get_user_key.assert_called_with("user")

    def test_get_failed_response__success(self):
        response = _get_failed_response("GET", "test", "Message")
        self.assertEqual(599, response.status_code)

    @patch('enmutils.lib.enm_user_2.requests.post')
    def test_verify_credentials__success(self, mock_post):
        response = Mock()
        response.cookies = {AUTH_COOKIE_KEY: "key"}
        mock_post.return_value = response
        self.assertEqual(True, verify_credentials("user", "pass", "url"))

    @patch('enmutils.lib.enm_user_2.requests.post')
    def test_verify_credentials__no_cookie(self, mock_post):
        response = Mock()
        response.cookies = {"cookie": "key"}
        mock_post.return_value = response
        self.assertEqual(False, verify_credentials("user", "pass", "url"))

    def test_build_user_message__json_message(self):
        response = Mock()
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"userMessage": "Msg"}
        self.assertEqual("Msg", build_user_message(response))

    def test_build_user_message__header_fields_insensitive(self):
        response = Mock()
        response.headers = {"content-length": 800, "Content-Type": "application/json"}
        response.json.return_value = {"userMessage": "Msg"}
        self.assertEqual("Msg", build_user_message(response))

    def test_build_user_message__text_message(self):
        response = Mock()
        response.headers = {"content-type": "text/html"}
        response.text = "Message"
        self.assertEqual("Message", build_user_message(response))

    @patch('enmutils.lib.enm_user_2.json.dumps', return_value="Msg")
    def test_build_user_message__json_message_no_user_message(self, mock_dumps):
        response = Mock()
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"message": "Msg"}
        build_user_message(response)
        self.assertEqual(1, mock_dumps.call_count)

    @patch('enmutils.lib.enm_user_2.json.dumps', return_value="Msg")
    def test_build_user_message__json_message_attribute_error(self, mock_dumps):
        response = Mock()
        response.headers = {"content-type": "application/json"}
        delattr(response, 'json')
        build_user_message(response)
        self.assertEqual(0, mock_dumps.call_count)

    @patch('enmutils.lib.enm_user_2.build_user_message')
    def test_raises_for_status__success(self, mock_message):
        response = Mock()
        response.status_code = 200
        raise_for_status(response)
        self.assertEqual(0, mock_message.call_count)

    @patch('enmutils.lib.enm_user_2.build_user_message', return_value="Msg")
    def test_raises_for_status__raises_http_error(self, _):
        response = Mock()
        response.status_code = 500
        self.assertRaises(HTTPError, raise_for_status, response)

    def test_verify_json_response__invalid_json_response(self):
        response = Mock()
        response.json.side_effect = ValueError("Response was not written in JSON format")
        self.assertRaises(EnmApplicationError, verify_json_response, response)

    # check_haproxy_online test cases
    @patch("enmutils.lib.enm_user_2.persistence.get", return_value=None)
    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.cache.is_emp", return_value=True)
    @patch("enmutils.lib.enm_user_2.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_ms")
    @patch("enmutils.lib.enm_user_2.shell.run_local_cmd")
    @patch("enmutils.lib.enm_user_2.shell.Command")
    @patch("enmutils.lib.enm_user_2.persistence.set")
    @patch("enmutils.lib.enm_user_2.cache.get_emp")
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_vm")
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    def test_check_haproxy_online__is_successful_on_cloud_openstack(self, mock_debug_log, mock_run_cmd_on_vm,
                                                                    mock_get_emp, mock_set, *_):
        cmd = ("sudo consul members | egrep $(sudo consul catalog nodes -service=haproxy| egrep -v Node | awk "
               "'{print $1}')")
        haproxy_status = "ieatenmc5b03-haproxy-0  10.10.0.93:8301 alive client 0.9.2 2 dc1\n"
        mock_get_emp.return_value = unit_test_utils.generate_configurable_ip()
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=haproxy_status)
        self.assertEqual(True, check_haproxy_online())
        mock_run_cmd_on_vm.assert_called_with(cmd, mock_get_emp.return_value)
        self.assertEqual(3, mock_debug_log.call_count)
        self.assertEqual(0, mock_set.call_count)

    @patch("enmutils.lib.enm_user_2.persistence.get", return_value=None)
    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.cache.is_emp", return_value=True)
    @patch("enmutils.lib.enm_user_2.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_ms")
    @patch("enmutils.lib.enm_user_2.shell.run_local_cmd")
    @patch("enmutils.lib.enm_user_2.shell.Command")
    @patch("enmutils.lib.enm_user_2.persistence.set")
    @patch("enmutils.lib.enm_user_2.cache.get_emp")
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_vm")
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    def test_check_haproxy_online__if_haproxy_inactive_on_cloud_openstack(self, mock_debug_log, mock_run_cmd_on_vm,
                                                                          mock_get_emp, mock_set, *_):
        cmd = ("sudo consul members | egrep $(sudo consul catalog nodes -service=haproxy| egrep -v Node | awk "
               "'{print $1}')")
        haproxy_status = "ieatenmc5b03-haproxy-0  10.10.0.93:8301 inactive client 0.9.2 2 dc1\n"
        mock_get_emp.return_value = unit_test_utils.generate_configurable_ip()
        mock_run_cmd_on_vm.return_value = Mock(rc=0, stdout=haproxy_status)
        self.assertEqual(False, check_haproxy_online())
        mock_run_cmd_on_vm.assert_called_with(cmd, mock_get_emp.return_value)
        self.assertEqual(3, mock_debug_log.call_count)
        self.assertEqual(1, mock_set.call_count)

    @patch("enmutils.lib.enm_user_2.persistence.get", return_value=None)
    @patch("enmutils.lib.enm_user_2.persistence.set")
    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.cache.is_emp", return_value=False)
    @patch("enmutils.lib.enm_user_2.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils.lib.enm_user_2.shell.run_local_cmd")
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_ms")
    @patch("enmutils.lib.enm_user_2.shell.Command")
    def test_check_haproxy_online__is_successful_on_physical(self, mock_command, mock_run_cmd_on_ms, mock_debug_log,
                                                             *_):
        cmd = HA_PROXY_ONLINE
        mock_command.return_value = Mock()
        haproxy_status = ("svc_cluster                       Grp_CS_svc_cluster_haproxy_ext  ieatrcxb6247  "
                          "active-standby          lsb        ONLINE          OK       -\n")
        mock_run_cmd_on_ms.return_value = Mock(rc=0, stdout=haproxy_status)
        self.assertEqual(True, check_haproxy_online())
        mock_command.assert_called_with(cmd)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch("enmutils.lib.enm_user_2.persistence.get", return_value=None)
    @patch("enmutils.lib.enm_user_2.persistence.set")
    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils.lib.enm_user_2.cache.is_emp", return_value=False)
    @patch("enmutils.lib.enm_user_2.shell.run_local_cmd")
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_ms")
    @patch("enmutils.lib.enm_user_2.shell.Command")
    def test_check_haproxy_online__if_ext_cluster_offline_on_physical(self, mock_command, mock_run_cmd_on_ms,
                                                                      mock_debug_log, *_):
        cmd = HA_PROXY_ONLINE
        mock_command.return_value = Mock()
        haproxy_status = " "
        mock_run_cmd_on_ms.return_value = Mock(rc=1, stdout=haproxy_status)
        self.assertEqual(False, check_haproxy_online())
        mock_command.assert_called_with(cmd)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch("enmutils.lib.enm_user_2.persistence.get", return_value=None)
    @patch("enmutils.lib.enm_user_2.persistence.set")
    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.cache.is_emp", return_value=False)
    @patch("enmutils.lib.enm_user_2.cache.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils.lib.enm_user_2.shell.run_local_cmd")
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    @patch("enmutils.lib.enm_user_2.shell.run_cmd_on_ms")
    @patch("enmutils.lib.enm_user_2.shell.Command")
    def test_check_haproxy_online__raises_exception_if_command_result_is_non_zero(
            self, mock_command, mock_run_cmd_on_ms, mock_debug_log, *_):
        cmd = HA_PROXY_ONLINE
        mock_command.return_value = Mock()
        mock_run_cmd_on_ms.return_value = Mock(rc=1)
        self.assertEqual(False, check_haproxy_online())
        mock_command.assert_called_with(cmd)
        mock_run_cmd_on_ms.assert_called_with(mock_command.return_value)
        self.assertEqual(3, mock_debug_log.call_count)

    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.cache.is_emp", return_value=False)
    @patch("enmutils.lib.enm_user_2.cache.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils.lib.enm_user_2.log.logger.debug")
    def test_check_haproxy_online__is_successful_on_cloud_native(self, mock_debug, *_):
        self.assertTrue(check_haproxy_online())
        self.assertTrue(call("ENM on Cloud native detected - HAproxy does not exist") in mock_debug.mock_calls)

    @patch("enmutils.lib.enm_user_2.mutexer.mutex")
    @patch("enmutils.lib.enm_user_2.persistence.get", return_value=False)
    def test_check_haproxy_online__uses_persisted_value(self, *_):
        self.assertEqual(False, check_haproxy_online())


class EnmRoleUnitTests2(unittest2.TestCase):

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    def setUp(self, _):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.response_json_roles = [{'name': 'test', 'status': 'ENABLED'}]
        self.role = EnmRole('test')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    def test__eq__success(self, _):
        self.role.name = 'test'
        mock_enm_role_other = EnmRole('test')
        mock_enm_role_other.name = 'test'
        self.assertEqual(True, self.role.__eq__(mock_enm_role_other))

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    def test__repr__success(self, _):
        self.role.name = 'test'
        self.assertEqual('test', self.role.__repr__())

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._delete')
    def test_teardown__success(self, mock_delete, _):
        self.role._teardown()
        mock_delete.assert_called_once_with()

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    @patch('enmutils.lib.enm_user_2.Target.get_existing_targets')
    def test_create__success(self, mock_get_existing_targets, mock_raise_for_status, _):
        self.role.user = mock_user = Mock()
        mock_target = Mock()
        mock_target1 = Mock()
        self.role.targets = mock_targets = [mock_target, mock_target1]
        mock_get_existing_targets.return_value = [mock_targets[:].pop(0)]
        self.role.name = 'test'
        self.role.description = 'test'
        self.role._create()
        mock_user.post.assert_called_with('/oss/idm/rolemanagement/roles',
                                          headers={'X-Requested-With': 'XMLHttpRequest'},
                                          json={'status': 'ENABLED', 'name': 'test', 'description': 'test'})
        mock_raise_for_status.assert_called_with(mock_user.post(), message_prefix='Could not create role: ')
        self.assertEqual(1, mock_get_existing_targets.call_count)

    @patch('enmutils.lib.enm_user_2.Target.get_existing_targets')
    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_create__success_with_additional_json(self, mock_raise_for_status, *_):
        self.role.user = mock_user = Mock()
        self.role.targets = [Mock()]
        self.role.name = 'test'
        self.role.description = 'test'
        mock_json = {'test': 'test'}
        self.role._create(additional_json=mock_json)
        mock_user.post.assert_called_with('/oss/idm/rolemanagement/roles',
                                          headers={'X-Requested-With': 'XMLHttpRequest'},
                                          json={'status': 'ENABLED', 'name': 'test', 'description': 'test',
                                                'test': 'test'})
        mock_raise_for_status.assert_called_with(mock_user.post(), message_prefix='Could not create role: ')

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_delete__success(self, mock_raise, mock_debug, _):
        self.role.name = 'test'
        self.role.user = mock_user = Mock()
        self.role._delete()
        mock_user.delete_request.assert_called_with('/oss/idm/rolemanagement/roles/test',
                                                    headers={'X-Requested-With': 'XMLHttpRequest'})
        mock_raise.assert_called_with(mock_user.delete_request(), message_prefix='Could not delete role: ')
        mock_debug.assert_called_with('Successfully deleted ENM Role test')

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_update__success_additional_json(self, *_):
        self.role.name = 'test_name'
        self.role.description = 'test_description'
        self.role.enabled = Mock()
        self.role.user = mock_user = Mock()
        mock_additional_json = {'test': 'test'}
        self.role._update(mock_additional_json)
        mock_user.put.assert_called_with('/oss/idm/rolemanagement/roles/test_name',
                                         headers={'X-Requested-With': 'XMLHttpRequest'},
                                         json={'status': 'ENABLED', 'test': 'test', 'type': 'custom',
                                               'name': 'test_name', 'description': 'test_description'})

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_update__success(self, mock_raise, mock_debug, _):
        self.role.name = 'test_name'
        self.role.description = 'test_description'
        self.role.enabled = Mock()
        self.role.user = mock_user = Mock()
        mock_additional_json = None
        self.role._update(mock_additional_json)
        mock_user.put.assert_called_with('/oss/idm/rolemanagement/roles/test_name',
                                         headers={'X-Requested-With': 'XMLHttpRequest'},
                                         json={'status': 'ENABLED', 'type': 'custom',
                                               'name': 'test_name', 'description': 'test_description'})
        mock_raise.assert_called_with(mock_user.put(), message_prefix='Could not update role: ')
        mock_debug.assert_called_with('Successfully updated ENM Role test_name')

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value={'name': 'test', 'description': 'test_desc', 'type': "system", 'status': 'ENABLED'})
    def test_get_role_by_name__success_enmrole(self, *_):
        self.assertIsInstance(EnmRole.get_role_by_name('test'), EnmRole)

    @patch('enmutils.lib.enm_user_2.EnmComRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value={'name': 'test', 'description': 'test_desc', 'type': "com", 'status': 'ENABLED'})
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm')
    def test_get_role_by_name__success_enmcomrole(self, *_):
        self.assertIsInstance(EnmRole.get_role_by_name('test'), EnmComRole)

    @patch('enmutils.lib.enm_user_2.EnmComRole')
    @patch('enmutils.lib.enm_user_2.EnmRoleAlias.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value={'name': 'test', 'description': 'test_desc', 'type': "comalias", 'status': 'ENABLED',
                         'roles': [MagicMock(name='test')]})
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm')
    def test_get_role_by_name__success_enmrolealias(self, *_):
        self.assertIsInstance(EnmRole.get_role_by_name('test'), EnmRoleAlias)

    @patch('enmutils.lib.enm_user_2.EnmComRole')
    @patch('enmutils.lib.enm_user_2.RoleCapability.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value={'name': 'test', 'description': 'test_desc', 'type': "test", 'status': 'ENABLED',
                         'policy': {}, 'roles': [MagicMock(name='test')]})
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm')
    def test_get_role_by_name__success_customrole(self, *_):
        self.assertIsInstance(EnmRole.get_role_by_name('test'), CustomRole)

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils.lib.enm_user_2.EnmRole')
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value=[{'name': 'test', 'description': 'test_desc', 'type': "system", 'status': 'ENABLED'}])
    def test_get_all_roles__success_enmrole(self, _, mock_enm_role, mock_admin):
        mock_enm_role.return_value = mock_enn_role_value = Mock()
        self.assertEqual({mock_enn_role_value}, EnmRole.get_all_roles(mock_admin))

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value=[{'name': 'test', 'description': 'test_desc', 'type': "com", 'status': 'ENABLED'}])
    @patch('enmutils.lib.enm_user_2.EnmComRole')
    def test_get_all_roles__success_enmcomrole(self, mock_enm_role, *_):
        self.assertEqual({mock_enm_role()}, EnmRole.get_all_roles())

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm',
           return_value=[{'name': 'test', 'description': 'test_desc', 'type': "test", 'status': 'ENABLED'}])
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_by_name')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_get_all_roles__success_not_cpp_and_com(self, mock_debug, mock_get_role_by_name, *_):
        self.assertEqual({mock_get_role_by_name()}, EnmRole.get_all_roles())
        mock_debug.assert_called_with("Getting all role objects from ENM")

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_check_if_role_exists__success(self, mock_debug, mock_get_enm_roles, _):
        mock_get_enm_roles.return_value = self.response_json_roles
        self.assertEqual(None, EnmRole.check_if_role_exists('test'))
        mock_debug.assert_called_with('Checking if role already exists on ENM')

    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_check_if_role_exists__returns_dict_if_no_role(self, mock_debug, mock_get_enm_roles):
        mock_get_enm_roles.return_value = self.response_json_roles
        self.assertEqual(self.response_json_roles, EnmRole.check_if_role_exists('test01'))
        mock_debug.assert_called_with('Checking if role already exists on ENM')

    @patch('enmutils.lib.enm_user_2.EnmRole.get_role_info_from_enm')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_get_all_role_names__success(self, mock_debug, mock_get_enm_roles):
        mock_get_enm_roles.return_value = self.response_json_roles
        self.assertEqual(['test'], EnmRole.get_all_role_names())
        mock_debug.assert_called_with('Getting names of all existing roles on ENM')

    @patch('enmutils.lib.enm_user_2.raise_for_status')
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    def test_get_role_info_from_enm__sucess(self, mock_debug, mock_raise):
        user = Mock()
        EnmRole.get_role_info_from_enm(user=user)
        user.get.assert_called_with('/oss/idm/rolemanagement/roles/', headers={'X-Requested-With': 'XMLHttpRequest'})
        mock_raise.assert_called_with(user.get(), message_prefix='Could not get ENM roles: ')
        mock_debug.assert_called_with('Getting existing roles from ENM endpoint')


class EnmComRoleUnitTests2(unittest2.TestCase):

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    def setUp(self, _):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.role = EnmComRole('test')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.Target')
    def test__init__success(self, mock_target, _):
        enm_com_role = EnmComRole('test')
        mock_target.assert_called_with("ALL")
        self.assertIsInstance(enm_com_role, EnmComRole)

    @patch('enmutils.lib.enm_user_2.EnmComRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._create')
    def test_create__success(self, mock_create, _):
        self.role.create()
        mock_create.assert_called_with(additional_json={'type': 'com'})

    @patch('enmutils.lib.enm_user_2.EnmComRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._delete')
    def test_delete__success(self, mock_delete, _):
        self.role.delete()
        mock_delete.assert_called_once_with()

    @patch('enmutils.lib.enm_user_2.EnmComRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._update')
    def test_update__success(self, mock_update, _):
        self.role.update()
        mock_update.assert_called_with(additional_json={"type": "com"})


class EnmRoleAliasUnitTests2(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.EnmRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.Target')
    def test__init__success(self, mock_target, _):
        mock_roles = Mock()
        enm_role_alias = EnmRoleAlias('test', mock_roles)
        mock_target.assert_called_with("ALL")
        self.assertIsInstance(enm_role_alias, EnmRoleAlias)
        self.assertEqual(mock_roles, enm_role_alias.roles)

    @patch('enmutils.lib.enm_user_2.EnmRoleAlias.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_all_role_names')
    @patch('enmutils.lib.enm_user_2.EnmRole._create')
    def test_create__success(self, mock_create, mock_get_all_role_names, _):
        mock_role = Mock()
        mock_role.name = 'test'
        mock_role_1 = Mock()
        mock_role_1.name = 'test1'
        mock_roles = {mock_role, mock_role_1}
        enm_role_alias = EnmRoleAlias('test_role_alias', mock_roles)
        enm_role_alias.roles = mock_roles
        mock_get_all_role_names.return_value = ['test']
        enm_role_alias.create()
        self.assertEqual(1, mock_create.call_count)

    @patch('enmutils.lib.enm_user_2.EnmRoleAlias.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._delete')
    def test_delete__success(self, mock_delete, _):
        mock_role_1 = Mock()
        mock_role_1.name = 'test1'
        mock_roles = {mock_role_1}
        enm_role_alias = EnmRoleAlias('test', mock_roles)
        enm_role_alias.delete()
        mock_delete.assert_called_once_with()


class CustomRoleUnitTests2(unittest2.TestCase):

    @patch('enmutils.lib.enm_user_2.CustomRole.__init__', return_value=None)
    def setUp(self, _):  # pylint: disable=arguments-differ
        unit_test_utils.setup()
        self.role = CustomRole('test')

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.EnmRole.get_all_role_names')
    @patch('enmutils.lib.enm_user_2.CustomRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.EnmRole._create')
    def test_create__success(self, mock_create, mock_debug, *_):
        self.role.user = Mock()
        self.role.name = 'test'
        mock_role = Mock()
        mock_capability = Mock()
        self.role.roles = [mock_role]
        self.role.capabilities = [mock_capability]
        self.role.create()
        self.assertEqual(1, mock_role.create.call_count)
        self.assertEqual(1, mock_create.call_count)
        mock_debug.assert_called_with('Attempting to create custom role: test')

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.CustomRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole.get_all_role_names')
    @patch('enmutils.lib.enm_user_2.EnmRole._create')
    def test_create__associated_role_not_created(self, mock_create, mock_get_all_role_names, *_):
        self.role.user = Mock()
        self.role.name = 'test'
        mock_role = Mock()
        mock_role.name = 'test'
        mock_capability = Mock()
        self.role.roles = [mock_role]
        mock_get_all_role_names.return_value = ['test']
        self.role.capabilities = [mock_capability]
        self.role.create()
        self.assertEqual(0, mock_role.create.call_count)
        self.assertEqual(1, mock_create.call_count)

    @patch('enmutils.lib.enm_user_2.CustomRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._delete')
    def test_delete__success(self, mock_delete, _):
        self.role.delete()
        mock_delete.assert_called_once_with()

    @patch('enmutils.lib.enm_user_2.CustomRole.__init__', return_value=None)
    @patch('enmutils.lib.enm_user_2.EnmRole._update')
    @patch('enmutils.lib.enm_user_2.EnmRole.get_all_role_names')
    def test_update__success(self, mock_get_all_role_names, mock_update, _):
        mock_role = Mock()
        mock_role.name = 'test'
        mock_role_1 = Mock()
        mock_role_1.name = 'test1'
        mock_roles = [mock_role, mock_role_1]
        self.role.roles = mock_roles
        mock_get_all_role_names.return_value = ['test1']
        mock_capability = Mock()
        self.role.capabilities = [mock_capability]
        self.role.user = Mock()
        self.role.update()
        mock_update.assert_called_with(
            additional_json={'policy': {mock_capability.resource: [mock_capability.operation]},
                             'type': 'custom', 'assignRoles': ['test', 'test1']})


class RoleCapabilityUnitTests2(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.enm_user_2.RoleCapability.__init__', return_value=None)
    def test__eq__success(self, _):
        role_capability = RoleCapability('test', 'test')
        role_capability.resource = 'test'
        role_capability.operation = 'test'
        other_role_capability = RoleCapability('test', 'test')
        other_role_capability.resource = 'test'
        other_role_capability.operation = 'test'
        self.assertEqual(True, role_capability.__eq__(other_role_capability))

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test__init__success(self, mock_admin):
        role_capability = RoleCapability('test', 'test', 'test')
        self.assertEqual('test', role_capability.resource)
        self.assertEqual('test', role_capability.operation)
        self.assertEqual('test', role_capability.description)
        mock_admin.assert_called_once_with()

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test__str__success(self, _):
        role_capability = RoleCapability('test', 'test', 'test')
        self.assertEqual("test:test", str(role_capability))

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test__hash__success(self, _):
        role_capability = RoleCapability('test', 'test', 'test')
        self.assertEqual(hash("test:test"), role_capability.__hash__())

    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test__repr__success(self, _):
        role_capability = RoleCapability('test', 'test', 'test')
        self.assertEqual("test:test", role_capability.__repr__())

    @patch('enmutils.lib.enm_user_2.raise_for_status')
    @patch('enmutils.lib.enm_user_2.get_admin_user')
    def test_get_all_role_capabilities__success(self, mock_admin, mock_raise):
        mock_admin.return_value = mock_admin_value = MagicMock()
        RoleCapability.get_all_role_capabilities()
        mock_admin_value.get.assert_called_with('/oss/idm/rolemanagement/usecases',
                                                headers={'X-Requested-With': 'XMLHttpRequest'})
        mock_raise.assert_called_with(mock_admin_value.get(), message_prefix='Could not get role capabilities: ')

    @patch('enmutils.lib.enm_user_2.RoleCapability.get_all_role_capabilities')
    def test_get_role_capabilities_for_resource__success(self, mock_all_capabilities):
        mock_capability = Mock(resource='test')
        mock_all_capabilities.return_value = [mock_capability]
        self.assertEqual(set([mock_capability]), RoleCapability.get_role_capabilities_for_resource('test'))

    @patch('enmutils.lib.enm_user_2.RoleCapability.get_all_role_capabilities')
    def test_get_role_capabilities_for_resource_based_on_operation__success(self, mock_all_capabilities):
        mock_all_capabilities.return_value = [Mock(resource='test', operation="read"),
                                              Mock(resource='test', operation="update")]
        self.assertEqual(set([mock_all_capabilities.return_value[0]]),
                         RoleCapability.get_role_capabilities_for_resource_based_on_operation('test', "read"))


class TargetUnitTests2(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.target = Target('test')

    def tearDown(self):
        unit_test_utils.tear_down()

    def test__init__success(self):
        self.assertEqual('test', self.target.name)
        self.assertEqual('', self.target.description)

    @patch('enmutils.lib.enm_user_2.Target.get_existing_targets')
    def test_exists__success(self, mock_all_targets):
        mock_target = Mock(name='test')
        mock_target.name = 'test'
        mock_all_targets.return_value = [Mock(), mock_target]
        self.assertEqual(True, self.target.exists)

    @patch('enmutils.lib.enm_user_2.Target.get_existing_targets')
    def test_exists__none_if_the_role_does_not_exist(self, mock_all_targets):
        mock_target = Mock()
        mock_all_targets.return_value = [Mock(), mock_target]
        self.assertEqual(None, self.target.exists)

    def test__eq__success(self):
        other_target = Target('test')
        self.assertEqual(True, self.target.__eq__(other_target))

    def test__str__success(self):
        self.assertEqual('test', str(self.target))

    def test__hash__success(self):
        self.assertEqual(hash('test'), self.target.__hash__())

    def test__repr__success(self):
        self.assertEqual('test', self.target.__repr__())

    @patch('enmutils.lib.enm_user_2.Target')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_get_existing_targets__success(self, mock_raise, mock_target):
        mock_user = MagicMock()
        mock_user.get().json.return_value = [{'name': 'test', 'description': 'test'}]
        self.assertEqual({mock_target()}, Target.get_existing_targets(mock_user))
        mock_user.get.assert_called_with('/oss/idm/targetgroupmanagement/targetgroups',
                                         headers={'X-Requested-With': 'XMLHttpRequest'})
        mock_raise.assert_called_with(mock_user.get(), message_prefix='Could not get ENM target groups: ')

    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_get_assigned_nodes__success(self, mock_raise):
        mock_user = self.target.user = MagicMock()
        mock_user.get().json.return_value = [{'name': 'test'}]
        self.assertEqual({'test'}, self.target.get_assigned_nodes())
        mock_user.get.assert_called_with('/oss/idm/targetgroupmanagement/targets?targetgroups=test',
                                         headers={'X-Requested-With': 'XMLHttpRequest'})
        mock_raise.assert_called_with(mock_user.get(),
                                      message_prefix="Could not get ENM target group's assigned nodes: ")

    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_create__success(self, mock_raise):
        mock_user = MagicMock()
        self.target.create(mock_user)
        mock_raise.assert_called_with(mock_user.post(), message_prefix='Could not create target group: ')
        mock_user.post.assert_any_call('/oss/idm/targetgroupmanagement/targetgroups',
                                       headers={'X-Requested-With': 'XMLHttpRequest'},
                                       json={'name': 'test', 'description': ''})

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_update__success(self, mock_raise, mock_debug):
        mock_user = MagicMock()
        self.target.update('test', mock_user)
        mock_raise.assert_called_with(mock_user.put(), message_prefix='Could not update target group: ')
        mock_user.put.assert_any_call('/oss/idm/targetgroupmanagement/targetgroups/test/description',
                                      headers={'X-Requested-With': 'XMLHttpRequest'}, json={'description': 'test'})
        mock_debug.assert_called_with("Successfully updated ENM Target Group {0}".format('test'))

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_update_assignment__success(self, mock_raise, mock_debug):
        mock_node = Mock()
        mock_node.node_id = 'test'
        mock_nodes = [mock_node]
        mock_user = MagicMock()
        self.target.update_assignment(mock_nodes, mock_user)
        mock_raise.assert_called_with(mock_user.put(), message_prefix='Could not update target group: ')
        mock_user.put.assert_any_call('/oss/idm/targetgroupmanagement/modifyassignment',
                                      headers={'X-Requested-With': 'XMLHttpRequest'},
                                      json=[{'action': 'ADD', 'targetGroup': 'test', 'target': 'test'}])
        mock_debug.assert_called_with("Successfully updated ENM Target Group {0}".format('test'))

    def test_update_assignment__raises_environ_error(self):
        mock_nodes = None
        mock_user = MagicMock()
        self.assertRaises(EnvironError, self.target.update_assignment, mock_nodes, mock_user)

    @patch('enmutils.lib.enm_user_2.log.logger.debug')
    @patch('enmutils.lib.enm_user_2.raise_for_status')
    def test_delete__success(self, mock_raise, mock_debug):
        mock_user = MagicMock()
        self.target.delete(mock_user)
        mock_raise.assert_called_with(mock_user.delete_request(), message_prefix="Could not delete target: ")
        mock_user.delete_request.assert_any_call('/oss/idm/targetgroupmanagement/targetgroups/test',
                                                 headers={'X-Requested-With': 'XMLHttpRequest'})
        mock_debug.assert_called_with("Successfully deleted ENM target group {0}".format('test'))

    @patch('enmutils.lib.enm_user_2.Target.delete')
    def test_teardown__success(self, mock_delete):
        self.target._teardown()
        mock_delete.assert_called_once_with()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
