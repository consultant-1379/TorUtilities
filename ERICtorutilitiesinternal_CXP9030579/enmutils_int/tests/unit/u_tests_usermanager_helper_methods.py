#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils.lib.enm_user_2 import EnmRole
from enmutils_int.lib.services import usermanager_helper_methods as helper
from testslib import unit_test_utils

USER_RESPONSE = [{u'username': u'ENMCLI_02_0729-07544075_u69', u'status': u'enabled', u'passwordResetFlag': False},
                 {u'username': u'ENMCLI_02_0729-07544075_u70', u'status': u'enabled', u'passwordResetFlag': False},
                 {u'username': u'ENMCLI_02_0729-07544075_u71', u'status': u'enabled', u'passwordResetFlag': False}]


class UserManagementHelperMethodsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_total_enm_user_count', return_value=5000)
    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    def test_check_user_count_threshold__success(self, *_):
        expected = ('Unable to complete user creation request, ENM maximum: 5000 user(s) capability reached.', 409)
        self.assertEqual(helper.check_user_count_threshold(), expected)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_total_enm_user_count',
           side_effect=Exception('some error'))
    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    def test_check_user_count_threshold__return_appropriate_message_rc_on_exception(self, *_):
        expected = ('Could not create user(s) on ENM due to :: some error.', 500)
        self.assertEqual(helper.check_user_count_threshold(), expected)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_total_enm_user_count', return_value=100)
    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    def test_check_user_count_threshold__success_if_user_count_less_than_threshold(self, *_):
        self.assertIsNone(helper.check_user_count_threshold())

    @patch('enmutils_int.lib.services.usermanager_helper_methods.mutexer.mutex')
    def test_get_total_enm_user_count__success(self, _):
        user, response, response1 = Mock(), Mock(), Mock()
        response.json.return_value = USER_RESPONSE
        response1.json.return_value = []
        user.get.side_effect = [response, response1]
        self.assertEqual(3, helper.get_total_enm_user_count(user, "path"))

    @patch('enmutils_int.lib.services.usermanager_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_get_total_enm_user_count__raises_enm_application_error(self, mock_debug, _):
        e_msg = "No such attribute."
        user, response = Mock(), Mock()
        response.json.side_effect = AttributeError(e_msg)
        user.get.side_effect = [response]
        self.assertRaises(helper.EnmApplicationError, helper.get_total_enm_user_count, user, "path")
        mock_debug.assert_called_with(e_msg)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.mutexer.mutex')
    def test_get_total_enm_user_count__raises_enm_application_error_if_user_count_zero(self, _):
        user, response, response1 = Mock(), Mock(), Mock()
        response.json.return_value = []
        response1.json.return_value = []
        user.get.side_effect = [response, response1]
        self.assertRaises(helper.EnmApplicationError, helper.get_total_enm_user_count, user, "path")

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_apache_url',
           side_effect=['enm_url.check.deployment', None])
    @patch('enmutils_int.lib.services.usermanager_helper_methods.cache.get', return_value='enm_url.check.cache')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.cache.set')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_fetch_and_set_enm_url_from_deploymentinfomanager__success(self, mock_debug, mock_set, *_):
        helper.fetch_and_set_enm_url_from_deploymentinfomanager()
        mock_debug.assert_any_call("Checking and updating ENM URL from deploymentinfomanager service")
        mock_debug.assert_any_call("Updating ENM URL for usermanager: 'enm_url.check.cache'"
                                   " to 'enm_url.check.deployment'")
        mock_set.assert_called_with("httpd-hostname", "enm_url.check.deployment")

        helper.fetch_and_set_enm_url_from_deploymentinfomanager()
        mock_debug.assert_any_call("Unable to fetch ENM URL from deploymentinfomanager service")

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_apache_url',
           return_value='https://enm_url.check.deployment')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.cache.get', return_value='enm_url.check.deployment')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.cache.set')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_fetch_and_set_enm_url_from_deploymentinfomanager__does_not_change_enm_url(self, mock_debug, mock_set, *_):
        helper.fetch_and_set_enm_url_from_deploymentinfomanager()
        mock_debug.assert_any_call("Checking and updating ENM URL from deploymentinfomanager service")
        mock_debug.assert_any_call("Usermanager and deploymentinfomanager services have same ENM URL")
        self.assertFalse(mock_set.called)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.User')
    def test_get_enm_users_list__success(self, mock_user, mock_get_workload_admin_user):
        helper.get_enm_users_list()
        mock_user.get_usernames.assert_called_with(user=mock_get_workload_admin_user.return_value)

    @patch('time.sleep', side_effect=lambda _: None)
    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.User.get_usernames',
           side_effect=[helper.SessionTimeoutException, []])
    @patch('enmutils_int.lib.services.usermanager_helper_methods.User')
    def test_get_enm_users_list__retries_on_session_timeout(self, mock_user, *_):
        helper.get_enm_users_list()
        self.assertEqual(mock_user.get_usernames.call_count, 2)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_enm_users_list',
           return_value=["TEST_01-12345", "TEST_01-23456", "TEST_02-34567"])
    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_user_privileges')
    def test_get_enm_users_with_matching_user_roles__successful(self, mock_get_user_privileges, _):
        role1, role2, role3 = Mock(), Mock(), Mock()
        role1.name, role2.name, role3.name = "Role1", "Role2", "Role3"

        user1_roles = [role1]
        user2_roles = [role2, role1]
        user3_roles = [role2]
        mock_get_user_privileges.side_effect = [user1_roles, user2_roles, user3_roles]

        role_1 = EnmRole("Role1", user="user")
        role_2 = EnmRole("Role2", user="user")

        self.assertEqual(helper.get_enm_users_with_matching_user_roles("TEST_01", [role_2, role_1]),
                         ["TEST_01-23456"])

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.User')
    def test_delete_users_from_enm_by_usernames__successful(
            self, mock_user, mock_get_workload_admin_user):
        helper.delete_users_from_enm_by_usernames(["TEST_01"])
        mock_user.assert_called_with(username="TEST_01")
        mock_user.return_value.delete.assert_called_with(delete_as=mock_get_workload_admin_user.return_value)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_all_sessions',
           return_value={'users': {'logviewer_01_1234': 4, 'cmimport_01_234j': 5, 'apache': 15}})
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_get_sessions_info__success(self, mock_debug, _):
        profile_name = ['logviewer_01', 'cmimport_01']
        expected = ({'logged_in': 3, 'logviewer_01': 4, 'total': 24, 'cmimport_01': 5},
                    [('apache', 15), ('cmimport_01_234j', 5), ('logviewer_01_1234', 4)])
        self.assertEqual(expected, helper.get_sessions_info(profile_name))
        mock_debug.assert_called_with('Total sessions found: 24. Total logged in users: 3')

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_all_sessions', side_effect=Exception('some error'))
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_get_sessions_info__failure_to_get_all_sessions(self, mock_debug, _):
        profile_name = ['logviewer_01', 'cmimport_01']
        expected = ({'logged_in': 'UNKNOWN', 'logviewer_01': 0, 'total': 'UNKNOWN', 'cmimport_01': 0}, None)
        self.assertEqual(expected, helper.get_sessions_info(profile_name))
        mock_debug.assert_any_call('Exception thrown while getting sessions. Exception: some error')
        mock_debug.assert_called_with('Total sessions found: UNKNOWN. Total logged in users: UNKNOWN')

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_enm_users_with_matching_user_roles',
           return_value=['test_username'])
    @patch('enmutils_int.lib.services.usermanager_helper_methods.delete_users_from_enm_by_usernames')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_check_delete_users__success(self, mock_debug, mock_delete_users, _):
        helper.delete_existing_users('test_profile', ['test_role'])

        mock_debug.assert_called_with("Attempting to delete ['test_username'] user(s) for [test_profile] profile")
        mock_delete_users.assert_called_once_with(['test_username'])

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_enm_users_with_matching_user_roles',
           return_value=[])
    @patch('enmutils_int.lib.services.usermanager_helper_methods.delete_users_from_enm_by_usernames')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.log.logger.debug')
    def test_check_delete_users__does_not_trigger_delete_function_when_no_user(self, mock_debug, mock_delete_users, _):
        helper.delete_existing_users('test_profile', ['test_role'])

        self.assertEqual(1, mock_debug.call_count)
        self.assertEqual(0, mock_delete_users.call_count)

    def test_get_users_info_list__success(self):
        mock_user = Mock()
        mock_user.username = 'test_username'
        mock_user.password = 'test_password'
        mock_user.keep_password = 'test_keep'
        mock_user.persist = 'test_persist'
        mock_user._session_key = 'test_session_key'
        mock_users = [mock_user]

        result = helper.generate_user_info_list(mock_users)

        expected_list = [{'username': 'test_username', 'keep_password': 'test_keep', 'password': 'test_password',
                          '_session_key': 'test_session_key', 'persist': 'test_persist'}]
        self.assertListEqual(expected_list, result)

    @patch('enmutils_int.lib.services.usermanager_helper_methods.get_workload_admin_user')
    @patch('enmutils_int.lib.services.usermanager_helper_methods.EnmRole')
    def test_create_user_role_objects__success(self, mock_enm_role, mock_get_workload_admin_user):
        mock_get_workload_admin_user.return_value = mock_admin = Mock()
        mock_enm_role.return_value = mock_role_object = Mock()
        mock_roles = ["test_role", "test_role_1"]
        self.assertEqual([mock_role_object], helper.create_user_role_objects(mock_roles))
        mock_enm_role.assert_any_call("test_role", user=mock_admin)
        mock_enm_role.assert_called_with("test_role_1", user=mock_admin)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
