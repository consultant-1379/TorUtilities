#!/usr/bin/env python
import unittest2
from mock import Mock, patch
from requests.exceptions import HTTPError

from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib import enm_user
from enmutils_int.lib.enm_user import (CustomUser, get_admin_user, get_or_create_admin_user, user_exists,
                                       create_workload_admin_user, get_workload_admin_user,
                                       create_workload_admin_user_instance_and_login, verify_workload_admin_user_login,
                                       create_password_for_workload_admin, recreate_deleted_user, get_user_info,
                                       workload_admin_with_hostname, store_workload_admin_creator_info_in_file)
from testslib import unit_test_utils


class EnmUserUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = CustomUser(username="TestUser")
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.enm_user.gethostname', return_value='host')
    def test_workload_admin_with_hostname__returns_global_variable_value(self, _):
        enm_user.WORKLOAD_ADMIN_USERNAME = "workload_admin_host"
        self.assertEqual(workload_admin_with_hostname(), 'workload_admin_host')

    @patch('enmutils_int.lib.enm_user.gethostname', return_value='hostname')
    def test_workload_admin_with_hostname__sets_global_variable(self, _):
        enm_user.WORKLOAD_ADMIN_USERNAME = None
        self.assertEqual(workload_admin_with_hostname(), 'workload_admin_hostname')
        self.assertEqual(enm_user.WORKLOAD_ADMIN_USERNAME, 'workload_admin_hostname')

    @patch('enmutils_int.lib.enm_user.enm_user_2.User.post')
    def test_create_custom_user(self, mock_post):
        response = Mock()
        user = User(username="Admin")
        response.status_code = 200
        mock_post.return_value = response
        self.user.create(create_as=user)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.post')
    def test_create_custom_user_raises_http_error(self, *_):
        role, target = Mock(), Mock()
        role.name = "admin"
        target.name = "all"
        self.user.roles = [role]
        self.user.targets = [target]
        self.assertRaises(HTTPError, self.user.create)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_or_create_admin_user')
    def test_get_or_create_admin_user(self, mock_get_or_create_admin_user):
        get_or_create_admin_user()
        self.assertEqual(mock_get_or_create_admin_user.call_count, 1)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    def test_get_admin_user(self, mock_get_admin_user):
        get_admin_user()
        self.assertEqual(mock_get_admin_user.call_count, 1)

    def test_user_exists(self):
        user, response = Mock(), Mock()
        response.ok = True
        user.get.return_value = response
        self.assertTrue(user_exists(search_as=user, search_for_username="Test"))
        response.ok = False
        user.get.return_value = response
        self.assertFalse(user_exists(search_as=user, search_for_username="Test"))

    @patch('enmutils_int.lib.enm_user.mutexer.mutex')
    @patch("enmutils_int.lib.enm_user.cache.check_if_on_workload_vm", return_value=True)
    @patch('enmutils_int.lib.enm_user.verify_workload_admin_user_login')
    @patch('enmutils_int.lib.enm_user.persistence.get')
    def test_get_workload_admin_user_persisted_user(self, mock_get, mock_persisted_user, *_):
        user = Mock()
        mock_get.return_value = user
        get_workload_admin_user()
        self.assertEqual(mock_persisted_user.call_count, 1)

    @patch('enmutils_int.lib.enm_user.get_local_ip_and_hostname', return_value=['ip', 'host'])
    @patch('enmutils_int.lib.enm_user.base64.b64encode')
    def test_create_password_for_workload_admin__returns_password(self, mock_base64, _):
        create_password_for_workload_admin()
        self.assertEqual(mock_base64.call_count, 2)

    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.get_local_ip_and_hostname')
    @patch('enmutils_int.lib.enm_user.base64.b64encode', return_value='=' * 33)
    def test_create_password_for_workload_admin__returns_password_default_pass(self, mock_base64, mock_host, mock_log):
        mock_host.return_value = ['ip_add', 'host_name_host_name_host_name']
        create_password_for_workload_admin()
        self.assertEqual(mock_base64.call_count, 2)
        mock_log.assert_called_with('Retrieving default password')

    @patch('enmutils_int.lib.enm_user.mutexer.mutex')
    @patch('enmutils_int.lib.enm_user.cache.set')
    @patch('enmutils_int.lib.enm_user.cache.get')
    @patch('enmutils_int.lib.enm_user.cache.has_key', return_value=False)
    @patch("enmutils_int.lib.enm_user.cache.check_if_on_workload_vm", return_value=True)
    @patch('enmutils_int.lib.enm_user.create_workload_admin_user_instance_and_login')
    @patch('enmutils_int.lib.enm_user.persistence.get')
    def test_get_workload_admin_user__gets_or_creates_workload_admin_user(self, mock_get, mock_create_user, *_):
        mock_get.return_value = None
        get_workload_admin_user()
        self.assertEqual(mock_create_user.call_count, 1)

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname', return_value="workload_admin_host")
    @patch('enmutils_int.lib.enm_user.User')
    @patch('enmutils_int.lib.enm_user.create_password_for_workload_admin')
    @patch('enmutils_int.lib.enm_user.verify_workload_admin_user_login')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_create_workload_admin_user_instance_and_login__is_successful(self, mock_debug, mock_login_user, *_):
        create_workload_admin_user_instance_and_login()
        mock_debug.assert_any_call('Creating the workload admin user instance.')
        self.assertEqual(mock_login_user.call_count, 1)

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_verify_workload_admin_user_login__is_successful(self, mock_debug, _):
        enm_user.WORKLOAD_ADMIN_USERNAME = "workload_admin_host"
        user = Mock()
        user.is_session_established.return_value = True
        verify_workload_admin_user_login(user)
        mock_debug.assert_called_with('Successfully retrieved the user workload_admin_host'
                                      ' from persistence and re-established session.')

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.enm_user_2.get_or_create_admin_user')
    @patch('enmutils_int.lib.enm_user.create_workload_admin_user')
    def test_verify_workload_admin_user_login__throws_invalid_login_exception(self, mock_create_user, *_):
        enm_user.WORKLOAD_ADMIN_USERNAME = "workload_admin_host"
        user = Mock()
        user.is_session_established.side_effect = Exception('Invalid login, credentials are invalid')
        verify_workload_admin_user_login(user)
        self.assertEqual(mock_create_user.call_count, 1)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_or_create_admin_user')
    @patch('enmutils_int.lib.enm_user.create_workload_admin_user')
    def test_verify_workload_admin_user_login__calls_create_workload_admin_if_invalid_enm_url(self, mock_create_user,
                                                                                              *_):
        user = Mock()
        user.is_session_established.side_effect = Exception('Exception: Failed to open session. Please make sure '
                                                            'the URL [url] is a valid ENM URL')
        verify_workload_admin_user_login(user)
        self.assertEqual(mock_create_user.call_count, 1)

    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_verify_workload_admin_user_login__throws_exception(self, mock_debug):
        user = Mock()
        user.is_session_established.side_effect = Exception('Exception')
        self.assertRaises(Exception, verify_workload_admin_user_login, user)
        mock_debug.assert_called_with("There has been an issue re-establishing the session. Error: Exception")

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.create_workload_admin_user')
    @patch('enmutils_int.lib.enm_user.enm_user_2.get_or_create_admin_user')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_verify_workload_admin_user_login__logs_exception(self, mock_debug, *_):
        enm_user.WORKLOAD_ADMIN_USERNAME = 'workload_admin_host'
        user = Mock()
        user.is_session_established.side_effect = Exception('valid ENM')
        verify_workload_admin_user_login(user)
        mock_debug.assert_called_with('Exception occurred: valid ENM. Starting creation of user workload_admin_host.')

    @patch('enmutils_int.lib.enm_user.mutexer.mutex')
    @patch('enmutils_int.lib.enm_user.cache.has_key', return_value=False)
    @patch('enmutils_int.lib.enm_user.cache.set')
    @patch("enmutils_int.lib.enm_user.cache.check_if_on_workload_vm", return_value=False)
    @patch('enmutils_int.lib.enm_user.enm_user_2.get_or_create_admin_user')
    @patch('enmutils_int.lib.enm_user.cache.get')
    def test_get_workload_admin_user__calls_defaults_admin_user(self, mock_get, mock_create, *_):
        get_workload_admin_user()
        self.assertEqual(mock_create.call_count, 1)
        self.assertEqual(mock_get.call_count, 1)

    @patch('enmutils_int.lib.enm_user.mutexer.mutex')
    @patch('enmutils_int.lib.enm_user.cache.has_key', return_value=True)
    @patch('enmutils_int.lib.enm_user.cache.set')
    @patch('enmutils_int.lib.enm_user.cache.get')
    def test_get_workload_admin_user__retrieves_the_cache_value_when_user_is_cached(self, mock_get, mock_set, *_):
        get_workload_admin_user()
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_set.call_count, 0)

    @patch('time.sleep')
    @patch('enmutils_int.lib.enm_user.get_local_ip_and_hostname', return_value=("ip", "host"))
    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.open_session')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.__init__', return_value=None)
    @patch('enmutils_int.lib.enm_user.store_workload_admin_creator_info_in_file')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.create')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_create_workload_admin_user(self, mock_debug, mock_create, mock_store_information, *_):
        enm_user.WORKLOAD_ADMIN_USERNAME = "workload_admin_host"
        user = Mock()
        create_workload_admin_user(user)
        mock_create.assert_called_with(create_as=user)
        mock_debug.assert_any_call("Successfully created user workload_admin_host.")
        self.assertTrue(mock_store_information.called)

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.get_local_ip_and_hostname', return_value=("ip", "host"))
    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.open_session')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.__init__', return_value=None)
    @patch('enmutils_int.lib.enm_user.store_workload_admin_creator_info_in_file')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.create', side_effect=[RuntimeError("Error"), None])
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_create_workload_admin_user__retries_on_runtime_error(self, mock_debug, mock_create,
                                                                  mock_store_information, *_):
        enm_user.WORKLOAD_ADMIN_USERNAME = "workload_admin_host"
        user = Mock()
        create_workload_admin_user(user)
        mock_create.assert_called_with(create_as=user)
        mock_debug.assert_any_call("Successfully created user workload_admin_host.")
        self.assertEqual(2, mock_create.call_count)
        self.assertTrue(mock_store_information.called)

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.get_human_readable_timestamp', return_value='11/11/2020 17:00:01')
    @patch('enmutils_int.lib.enm_user.getpid', return_value=1234)
    @patch('enmutils_int.lib.enm_user.write_data_to_file', return_value=True)
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_store_workload_admin_creator_info_in_file__success(self, mock_debug, mock_write_to_file, *_):
        enm_user.WORKLOAD_ADMIN_USERNAME = 'workload_admin_hostname'
        file_path = '/home/enmutils/.workload-admin-creation-info'
        store_workload_admin_creator_info_in_file()
        mock_write_to_file.assert_called_with('11/11/2020 17:00:01\tUser workload_admin_hostname '
                                              'created by process 1234\n', file_path, append=True)
        mock_debug.assert_any_call("Storing workload admin creation info in {0}".format(file_path))
        mock_debug.assert_any_call("Successlly stored information about workload admin creation.")

    @patch('enmutils_int.lib.enm_user.workload_admin_with_hostname')
    @patch('enmutils_int.lib.enm_user.get_human_readable_timestamp', return_value='11/11/2020 17:00:01')
    @patch('enmutils_int.lib.enm_user.getpid', return_value=1234)
    @patch('enmutils_int.lib.enm_user.write_data_to_file', return_value=False)
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    def test_store_workload_admin_creator_info_in_file__unable_to_append_logs(self, mock_debug, mock_write_to_file, *_):
        enm_user.WORKLOAD_ADMIN_USERNAME = 'workload_admin_hostanme'
        file_path = '/home/enmutils/.workload-admin-creation-info'
        store_workload_admin_creator_info_in_file()
        mock_write_to_file.assert_called_with('11/11/2020 17:00:01\tUser workload_admin_hostanme created '
                                              'by process 1234\n', file_path, append=True)
        mock_debug.assert_any_call("Storing workload admin creation info in {0}".format(file_path))
        mock_debug.assert_any_call("Failed to store information related to workload admin creation.")

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.get_user_info')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.create')
    def test_recreate_deleted_user__is_successful(self, mock_create_user, mock_get_user_info, mock_debug_log, *_):
        mock_get_user_info.return_value = None
        recreate_deleted_user("TestUser", ["PKI_Administrator"])
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_get_user_info.called)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.get_user_info')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.create')
    def test_create_deleted_user__if_user_not_found(self, mock_create_user, mock_get_user_info, mock_debug_log, *_):
        mock_get_user_info.side_effect = HTTPError("user not existed")
        recreate_deleted_user("TestUser", ["PKI_Administrator"])
        self.assertTrue(mock_create_user.called)
        self.assertTrue(mock_get_user_info.called)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.get_user_info')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.create')
    def test_create_deleted_user__if_user_existed(self, mock_create_user, mock_get_user_info, mock_debug_log, *_):
        mock_get_user_info.return_value = {u'username': u'TestUser', u'status': u'enabled',
                                           u'passwordResetFlag': False, u'surname': u'TestUser',
                                           u'name': u'TestUser', u'privileges': [],
                                           u'previousLogin': None, u'failedLogins': 0,
                                           u'maxSessionTime': None, u'maxIdleTime': None,
                                           u'passwordChangeTime': u'20200609104250+0000',
                                           u'authMode': u'local', u'lastLogin': u'20200609104256+0000',
                                           u'password': u'********',
                                           u'email': u'SECUI_06_0609-11425048_u0@ericsson.com',
                                           u'passwordAgeing': None, u'description': u''}
        recreate_deleted_user("TestUser", ["PKI_Administrator"])
        self.assertFalse(mock_create_user.called)
        self.assertFalse(mock_debug_log.called)
        self.assertTrue(mock_get_user_info.called)

    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.get_user_info')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.create')
    def test_create_deleted_user__raises_enm_application_error(self, mock_create_user, mock_get_user_info,
                                                               mock_debug_log, *_):
        mock_get_user_info.side_effect = HTTPError("user not existed")
        mock_create_user.side_effect = EnmApplicationError("User creation failed")
        self.assertRaises(EnmApplicationError, recreate_deleted_user, "TestUser", ["PKI_Administrator"])
        self.assertTrue(mock_create_user.called)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertTrue(mock_get_user_info.called)

    @patch('enmutils_int.lib.enm_user.enm_user_2.User.get')
    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    def test_get_user_info__is_successful(self, mock_get_admin_user, mock_debug_log, *_):
        response = Mock(ok=True)
        response.json.return_value = {"username": "TestUser"}
        mock_get_admin_user.return_value.get.return_value = response
        get_user_info("TestUser")
        self.assertTrue(mock_debug_log.called)

    @patch('enmutils_int.lib.enm_user.log.logger.debug')
    @patch('enmutils_int.lib.enm_user.enm_user_2.User.get')
    @patch('enmutils_int.lib.enm_user.enm_user_2.get_admin_user')
    def test_get_user_info__raises_http_error(self, mock_get_admin_user, mock_debug_log, *_):
        mock_get_admin_user.return_value.get.return_value = Mock(ok=False)
        self.assertRaises(HTTPError, get_user_info, "TestUser")
        self.assertFalse(mock_debug_log.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
