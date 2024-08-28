#!/usr/bin/env python
import json

import unittest2
from mock import patch, Mock

from enmutils_int.lib.services import usermanager_adaptor
from testslib import unit_test_utils


class UserManagerAdaptorUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.services.usermanager_adaptor.service_registry.get_service_info_for_service_name",
           return_value=('5007', 'test_host', Mock()))
    @patch("enmutils_int.lib.services.usermanager_adaptor.get_users_via_service")
    @patch("enmutils_int.lib.services.usermanager_adaptor.delete_users_via_service")
    @patch("enmutils_int.lib.services.usermanager_adaptor.convert_received_data_to_profile_users")
    @patch("enmutils_int.lib.services.usermanager_adaptor.send_request_to_service")
    def test_create_users_via_usermanager_service__success_list(self, mock_send_request, mock_convert_data_to_users,
                                                                mock_delete, mock_get_users, _):
        mock_send_request.return_value = mock_response = Mock(text="[{'user2': 'test'}, {'user1': 'test'}]")
        usermanager_adaptor.create_users_via_usermanager_service('test_profile', 2, ['test_role'])
        mock_send_request.assert_called_with('POST', 'users/create', json_data={
            'number_of_users': 2, 'username_prefix': 'test_profile', 'user_roles': ['test_role']})
        mock_send_request.assert_called_with('POST', 'users/create', json_data={
            'number_of_users': 2, 'username_prefix': 'test_profile', 'user_roles': ['test_role']})
        mock_convert_data_to_users.assert_called_with(mock_response)
        mock_get_users.assert_called_once_with('test_profile', roles=['test_role'])
        mock_delete.assert_called_once_with('test_profile', roles=['test_role'])

    @patch("enmutils_int.lib.services.usermanager_adaptor.service_registry.get_service_info_for_service_name",
           return_value=('5007', 'test_host', Mock()))
    @patch("enmutils_int.lib.services.usermanager_adaptor.delete_users_via_service")
    @patch("enmutils_int.lib.services.usermanager_adaptor.get_users_via_service")
    @patch("enmutils_int.lib.services.usermanager_adaptor.convert_received_data_to_profile_users")
    @patch("enmutils_int.lib.services.usermanager_adaptor.send_request_to_service")
    def test_create_users_via_usermanager_service__success_response(self, mock_send_request, mock_convert_data_to_users,
                                                                    mock_get_users, mock_delete, _):
        mock_send_request.return_value = Mock(text="test")
        mock_get_users.side_effect = [None, [Mock()]]
        usermanager_adaptor.create_users_via_usermanager_service('test_profile', 2, ['test_role'])
        mock_send_request.assert_called_with(
            'POST', 'users/create', json_data={'number_of_users': 2, 'username_prefix': 'test_profile',
                                               'user_roles': ['test_role']})
        mock_get_users.assert_called_with('test_profile', roles=['test_role'])
        self.assertEqual(2, mock_get_users.call_count)
        self.assertEqual(0, mock_convert_data_to_users.call_count)
        self.assertEqual(0, mock_delete.call_count)

    @patch("enmutils_int.lib.services.usermanager_adaptor.send_request_to_service")
    def test_delete_users_via_service__is_successful(self, mock_send_request_to_service):
        username_prefix = "PM_XX"
        user_roles = ["ADMIN"]
        usermanager_adaptor.delete_users_via_service(username_prefix, roles=user_roles)
        mock_send_request_to_service.assert_called_with('DELETE', "users/delete?delete_data={'profile_name': 'PM_XX', "
                                                                  "'user_roles': 'ADMIN'}")

    @patch("enmutils_int.lib.services.usermanager_adaptor.send_request_to_service")
    def test_delete_users_via_service__is_successful_no_roles(self, mock_send_request_to_service):
        username_prefix = "PM_XX"
        usermanager_adaptor.delete_users_via_service(username_prefix)
        mock_send_request_to_service.assert_called_with('DELETE', "users/delete?delete_data={'profile_name': 'PM_XX'}")

    @patch("enmutils_int.lib.services.usermanager_adaptor.convert_received_data_to_profile_users")
    @patch("enmutils_int.lib.services.usermanager_adaptor.send_request_to_service")
    def test_get_users_via_service__is_successful(
            self, mock_send_request_to_service, mock_convert_received_data_to_profile_users):
        username_prefix = "PM_XX"
        user = {"username": "PM_XX_07051044_u0", "keep_password": "true", "password": "TestPassw0rd",
                "_session_key": "blah-di-blah", "persist": "false"}
        service_response_text = u'[{0}]'.format(json.dumps(user))
        mock_response = Mock(ok=200, text=service_response_text)
        mock_send_request_to_service.return_value = mock_response
        get_users_url = "users?profile=PM_XX"

        mock_convert_received_data_to_profile_users.return_value = [user]
        users = usermanager_adaptor.get_users_via_service(username_prefix)
        self.assertEqual(users, [user])
        mock_send_request_to_service.assert_called_with("GET", get_users_url)
        mock_convert_received_data_to_profile_users.assert_called_with(mock_response)

    @patch("enmutils_int.lib.services.usermanager_adaptor.convert_received_data_to_profile_users")
    @patch("enmutils_int.lib.services.usermanager_adaptor.send_request_to_service")
    def test_get_users_via_service__is_successful_if_roles_specified(
            self, mock_send_request_to_service, mock_convert_received_data_to_profile_users):
        username_prefix = "PM_XX"
        user = {"username": "PM_XX_07051044_u0", "keep_password": "true", "password": "TestPassw0rd",
                "_session_key": "blah-di-blah", "persist": "false"}
        service_response_text = u'[{0}]'.format(json.dumps(user))
        mock_response = Mock(ok=200, text=service_response_text)
        mock_send_request_to_service.return_value = mock_response
        get_users_url = "users?profile=PM_XX&user_roles=ADMIN_ROLE1,ADMIN_ROLE2"

        mock_convert_received_data_to_profile_users.return_value = [user]
        users = usermanager_adaptor.get_users_via_service(username_prefix, roles=["ADMIN_ROLE1", "ADMIN_ROLE2"])
        self.assertEqual(users, [user])
        mock_send_request_to_service.assert_called_with("GET", get_users_url)
        mock_convert_received_data_to_profile_users.assert_called_with(mock_response)

    @patch("enmutils_int.lib.services.usermanager_adaptor.delete_users_via_service")
    @patch("enmutils_int.lib.services.usermanager_adaptor.service_registry.get_service_info_for_service_name")
    def test_delete_users_via_usermanager_service__is_successful(
            self, mock_get_service_info_for_service_name, mock_delete_users_via_service):
        mock_get_service_info_for_service_name.return_value = (5001, "localhost", 10)

        profile_name = "PM_XX"

        usermanager_adaptor.delete_users_via_usermanager_service(profile_name)
        mock_delete_users_via_service.assert_called_with(profile_name)
        mock_delete_users_via_service.assert_called_with(profile_name)

    @patch("json.loads")
    def test_convert_received_data_to_profile_users__is_successful_response_text(self, mock_loads):
        user_data = [{u'username': u'user1', u'keep_password': True, u'password': u'password1', u'persist': False,
                      u'_session_key': u'blah1'},
                     {u'username': u'user2', u'keep_password': True, u'password': u'password2', u'persist': False,
                      u'_session_key': u'blah2'}]

        response = Mock()
        mock_loads.return_value = user_data
        users = usermanager_adaptor.convert_received_data_to_profile_users(response)
        self.assertEqual("user1", users[0].username)
        self.assertEqual("password1", users[0].password)
        self.assertEqual("blah1", users[0]._session_key)
        self.assertEqual("user2", users[1].username)
        self.assertEqual("password2", users[1].password)
        self.assertEqual("blah2", users[1]._session_key)

    @patch("enmutils_int.lib.services.usermanager_adaptor.service_adaptor.send_request_to_service")
    def test_send_request_to_service__success(self, mock_send_request):
        usermanager_adaptor.send_request_to_service("POST", "users", {"username_prefix": "TEST_01",
                                                                      "number_of_users": 1,
                                                                      "user_roles": ["ADMINISTRATOR"]})
        mock_send_request.assert_called_with("POST", "users", usermanager_adaptor.SERVICE_NAME,
                                             json_data={"username_prefix": "TEST_01", "number_of_users": 1,
                                                        "user_roles": ["ADMINISTRATOR"]})

    @patch("enmutils_int.lib.services.usermanager_adaptor.service_adaptor.can_service_be_used", return_value=True)
    def test_check_if_service_can_be_used_by_profile__is_successful(self, mock_can_service_be_used):
        profile = Mock()
        self.assertTrue(usermanager_adaptor.check_if_service_can_be_used_by_profile(profile))
        mock_can_service_be_used.assert_called_with("usermanager", profile=profile)

    @patch('enmutils_int.lib.services.usermanager_adaptor.log.logger.debug')
    @patch("enmutils_int.lib.services.usermanager_adaptor.service_adaptor.can_service_be_used", return_value=True)
    @patch("enmutils_int.lib.services.usermanager_adaptor.service_adaptor.send_request_to_service")
    def test_get_profile_sessions_info__success_service_available(self, mock_send_request, *_):
        mock_profile_objects = [Mock(NAME='logviewer_01')]
        usermanager_adaptor.get_profile_sessions_info(mock_profile_objects)
        mock_send_request.assert_called_with('POST', 'users/sessions', 'usermanager',
                                             json_data={'profiles': ['logviewer_01']})
        mock_send_request().json().get().get.assert_any_call('profile_sessions')
        mock_send_request().json().get().get.assert_any_call('session_hoarders')

    @patch("enmutils_int.lib.services.usermanager_adaptor.service_adaptor.can_service_be_used", return_value=False)
    @patch("enmutils_int.lib.services.usermanager_adaptor.get_sessions_info", return_value=({'test'}, ['test']))
    @patch('enmutils_int.lib.services.usermanager_adaptor.log.logger.debug')
    def test_get_profile_sessions_info__success_service_not_available(self, *_):
        mock_profile_objects = [Mock(NAME='logviewer_01')]
        self.assertEqual(({'test'}, ['test']), usermanager_adaptor.get_profile_sessions_info(mock_profile_objects))


class BasicUserUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.services.usermanager_adaptor.deploymentinfomanager_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.services.usermanager_adaptor.cache_int.set_ttl')
    @patch('enmutils_int.lib.services.usermanager_adaptor.deploymentinfomanager_adaptor.get_apache_url',
           return_value="some_enm_address")
    def test_get_apache_url_from_service__uses_service(self, mock_get_apache, mock_set_ttl, _):
        self.assertEqual("some_enm_address", usermanager_adaptor.BasicUser.get_apache_url_from_service())
        self.assertEqual(1, mock_get_apache.call_count)
        mock_set_ttl.assert_called_with("ENM_URL", "some_enm_address")

    @patch('enmutils_int.lib.services.usermanager_adaptor.deploymentinfomanager_adaptor.can_service_be_used',
           return_value=False)
    @patch('enmutils_int.lib.services.usermanager_adaptor.cache_int.set_ttl')
    @patch('enmutils_int.lib.services.usermanager_adaptor.deploymentinfomanager_adaptor.get_apache_url')
    @patch('enmutils_int.lib.services.usermanager_adaptor.cache.get_apache_url', return_value="some_enm_address")
    def test_get_apache_url_from_service__defaults_to_legacy(self, mock_cache, mock_get_apache, mock_set_ttl, _):
        self.assertEqual("some_enm_address", usermanager_adaptor.BasicUser.get_apache_url_from_service())
        self.assertEqual(0, mock_get_apache.call_count)
        self.assertEqual(1, mock_cache.call_count)
        mock_set_ttl.assert_called_with("ENM_URL", "some_enm_address")

    @patch('enmutils_int.lib.services.usermanager_adaptor.deploymentinfomanager_adaptor.can_service_be_used',
           return_value=True)
    @patch('enmutils_int.lib.services.usermanager_adaptor.deploymentinfomanager_adaptor.get_apache_url',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.services.usermanager_adaptor.cache_int.set_ttl')
    @patch('enmutils_int.lib.services.usermanager_adaptor.log.logger.debug')
    def test_get_apache_url_from_service__logs_apache_exception(self, mock_debug, mock_set_ttl, *_):
        usermanager_adaptor.BasicUser.get_apache_url_from_service()
        mock_debug.assert_called_with("Unable to retrieve Apache URL, error encountered: [Error].")
        self.assertFalse(mock_set_ttl.called)

    @patch('enmutils_int.lib.services.usermanager_adaptor.BasicUser.__init__', return_value=None)
    @patch('enmutils_int.lib.services.usermanager_adaptor.mutexer.mutex')
    @patch('enmutils_int.lib.services.usermanager_adaptor.cache_int.get_ttl', return_value=None)
    @patch('enmutils_int.lib.services.usermanager_adaptor.User.open_session')
    @patch('enmutils_int.lib.services.usermanager_adaptor.BasicUser.get_apache_url_from_service',
           return_value="some_enm_url")
    def test_open_session__retrieves_apache_url_when_not_cached_in_memory(
            self, mock_get_apache, mock_open_session, mock_get_ttl, *_):
        user = usermanager_adaptor.BasicUser(**{})
        user.open_session()
        self.assertEqual(1, mock_get_apache.call_count)
        mock_open_session.assert_called_with(reestablish=False, url="some_enm_url")
        self.assertTrue(mock_get_ttl.called)

    @patch('enmutils_int.lib.services.usermanager_adaptor.BasicUser.__init__', return_value=None)
    @patch('enmutils_int.lib.services.usermanager_adaptor.mutexer.mutex')
    @patch('enmutils_int.lib.services.usermanager_adaptor.cache_int.get_ttl', return_value="some_enm_url")
    @patch('enmutils_int.lib.services.usermanager_adaptor.User.open_session')
    @patch('enmutils_int.lib.services.usermanager_adaptor.BasicUser.get_apache_url_from_service')
    def test_open_session__retrieves_apache_url_when_cached_in_memory(
            self, mock_get_apache, mock_open_session, mock_get_ttl, *_):
        user = usermanager_adaptor.BasicUser(**{})
        user.open_session()
        self.assertEqual(0, mock_get_apache.call_count)
        mock_open_session.assert_called_with(reestablish=False, url="some_enm_url")
        self.assertTrue(mock_get_ttl.called)

    def test_basic_user__overrides__str__and__repr__as_expected(self):
        username = "TEST_USER"
        user = usermanager_adaptor.BasicUser(**{"username": username})
        self.assertEqual(username, str(user))
        self.assertEqual(username, user.__repr__())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
