#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.external_session import (ExternalSession, HTTPError, UsernameAndPassword, is_password_change_redirect,
                                           AUTH_COOKIE_KEY, AUTHENTICATION_TIMEOUT, build_user_message)
from mock import Mock, patch, call
from requests import ConnectionError, Timeout
from testslib import unit_test_utils


class ExternalSessionUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_url__returns_correct_url(self):
        session = ExternalSession(url="test")
        self.assertEqual("test", session.url())

    def test_open_session__calls_authenticator(self):
        session = ExternalSession(url="test")
        authenticator = Mock()
        session.open_session(authenticator)
        self.assertEqual(1, authenticator.authenticate.call_count)

    def test_open_session__no_authenticator(self):
        session = ExternalSession(url="test")
        authenticator = Mock()
        session.open_session(None)
        self.assertEqual(0, authenticator.authenticate.call_count)

    @patch('enmutils.lib.external_session.ExternalSession.__init__', return_value=None)
    @patch('enmutils.lib.external_session.ExternalSession.close')
    def test_close_session__success(self, mock_close, _):
        session = ExternalSession(url="test")
        cookies = Mock()
        session._authenticator = None
        session.cookies = cookies
        session.close_session()
        self.assertEqual(1, mock_close.call_count)

    @patch('enmutils.lib.external_session.ExternalSession.__init__', return_value=None)
    @patch('enmutils.lib.external_session.ExternalSession.close')
    def test_close_session__logouts_authenticator_and_clears_cookies(self, mock_close, _):
        session = ExternalSession(url="test")
        authenticator = Mock()
        session._authenticator = authenticator
        cookies = Mock()
        session.cookies = cookies
        session.close_session()
        self.assertEqual(1, authenticator.logout.call_count)
        self.assertEqual(1, mock_close.call_count)
        self.assertEqual(1, cookies.clear_session_cookies.call_count)

    @patch('enmutils.lib.external_session.ExternalSession.__init__', return_value=None)
    @patch('enmutils.lib.external_session.UsernameAndPassword.logout')
    @patch('enmutils.lib.external_session.ExternalSession.close')
    def test_close_session__logouts_if_username_and_password_supplied(self, mock_close, mock_logout, _):
        session = ExternalSession(url="test")
        session._authenticator = None
        cookies = Mock()
        session.cookies = cookies
        session.close_session(username="user", password="pass")
        self.assertEqual(1, mock_logout.call_count)
        self.assertEqual(1, mock_close.call_count)
        self.assertEqual(1, cookies.clear_session_cookies.call_count)

    def test_authenticator__return_correct_authenticator(self):
        session = ExternalSession(url="test")
        self.assertEqual(None, session.authenticator())
        authenticator = Mock()
        session.open_session(authenticator)
        self.assertEqual(authenticator, session.authenticator())

    # post test cases
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.post')
    def test_post__success(self, mock_post, mock_build_user_message, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Success")
        mock_post.return_value = response
        post_response = session.post("url")
        self.assertEqual(post_response.status_code, 200)
        self.assertFalse(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.post')
    def test_post__raises_http_error(self, mock_post, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=404, text="Error")
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"userMessage": "Msg"}
        mock_post.return_value = response
        mock_build_user_message.return_value = "Msg"
        self.assertRaises(HTTPError, session.post, "url")
        self.assertTrue(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.post')
    def test_post__raises_http_error_if_bad_response(self, mock_post, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=502, reason="Proxy Error")
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"userMessage": "Msg"}
        mock_post.return_value = response
        mock_build_user_message.return_value = "Msg"
        self.assertRaises(HTTPError, session.post, "url")
        self.assertTrue(mock_build_user_message.called)

    # get test cases
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.get')
    def test_get__success(self, mock_get, mock_build_user_message, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Success")
        response.url = "url"
        response.is_redirect = False
        mock_get.return_value = response
        get_response = session.get("url")
        self.assertEqual(get_response.status_code, 200)
        self.assertFalse(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.get')
    def test_get__raises_http_error(self, mock_get, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=404, text="Error")
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"userMessage": "Msg"}
        response.raise_for_status.side_effect = HTTPError("Error")
        response.url = "url"
        response.is_redirect = False
        mock_get.return_value = response
        mock_build_user_message.return_value = "Msg"
        self.assertRaises(HTTPError, session.get, "url")
        self.assertTrue(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.get')
    def test_get__raises_http_error_if_login_url_redirect_detected(self, mock_get, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url/login/?goto"
        response.is_redirect = False
        mock_get.return_value = response
        self.assertRaises(HTTPError, session.get, "url")
        self.assertFalse(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.get')
    def test_get__raises_http_error_if_redirect_detected(self, mock_get, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url"
        response.is_redirect = True
        mock_get.return_value = response
        self.assertRaises(HTTPError, session.get, "url")
        self.assertFalse(mock_build_user_message.called)

    # put test cases
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.put')
    def test_put__success(self, mock_put, mock_build_user_message, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Success")
        response.url = "url"
        response.is_redirect = False
        mock_put.return_value = response
        get_response = session.put("url")
        self.assertEqual(get_response.status_code, 200)
        self.assertFalse(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.put')
    def test_put__raises_http_error(self, mock_put, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=404, text="Error", headers={"content-type": "application/json"})
        response.json.return_value = {"userMessage": "Msg"}
        response.raise_for_status.side_effect = HTTPError("Error")
        response.url = "url"
        response.is_redirect = False
        mock_put.return_value = response
        mock_build_user_message.return_value = "Msg"
        self.assertRaises(HTTPError, session.put, "url")
        self.assertTrue(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.put')
    def test_put__raises_http_error_if_login_url_redirect_detected(self, mock_put, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url/login/?goto"
        response.is_redirect = False
        mock_put.return_value = response
        self.assertRaises(HTTPError, session.put, "url")
        self.assertFalse(mock_build_user_message.called)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.build_user_message')
    @patch('enmutils.lib.external_session.Session.put')
    def test_put__raises_http_error_if_redirect_detected(self, mock_put, mock_build_user_message, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url"
        response.is_redirect = True
        mock_put.return_value = response
        self.assertRaises(HTTPError, session.put, "url")
        self.assertFalse(mock_build_user_message.called)

    # delete test cases
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.delete')
    def test_delete__is_successful(self, mock_delete, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Success")
        response.url = "url"
        response.is_redirect = False
        mock_delete.return_value = response
        get_response = session.delete("url")
        self.assertEqual(get_response.status_code, 200)

    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.delete')
    def test_delete__raises_http_error(self, mock_delete, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=404, text="Error")
        response.raise_for_status.side_effect = HTTPError("Error")
        response.url = "url"
        response.is_redirect = False
        mock_delete.return_value = response
        self.assertRaises(HTTPError, session.delete, "url")

    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.delete')
    def test_delete__raises_http_error_if_login_url_redirect_detected(self, mock_delete, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url/login/?goto"
        response.is_redirect = False
        mock_delete.return_value = response
        self.assertRaises(HTTPError, session.delete, "url")

    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.log.logger.debug')
    @patch('enmutils.lib.external_session.Session.delete')
    def test_delete__raises_http_error_and_logs_user_message(self, mock_delete, mock_debug, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=404, text='{"userMessage":"test message"}')
        response.raise_for_status.side_effect = HTTPError("Error")
        response.url = "url"
        response.reason = 'some_reason'
        response.is_redirect = False
        mock_delete.return_value = response
        self.assertRaises(HTTPError, session.delete, "url")
        mock_debug.assert_called_with('DELETE request to [url] has failed,\nresponse.status_code\t404, '
                                      'response.reason\tsome_reason, Message: test message')

    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.delete')
    def test_delete__raises_http_error_if_redirect_detected(self, mock_delete, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url"
        response.is_redirect = True
        mock_delete.return_value = response
        self.assertRaises(HTTPError, session.delete, "url")

    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.patch')
    def test_patch__success(self, mock_patch, _):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Success")
        response.url = "url"
        response.is_redirect = False
        mock_patch.return_value = response
        get_response = session.patch("url")
        self.assertEqual(get_response.status_code, 200)

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.patch')
    def test_patch__raises_http_error(self, mock_patch, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=404, text="Error")
        response.raise_for_status.side_effect = HTTPError("Error")
        response.url = "url"
        response.is_redirect = False
        mock_patch.return_value = response
        self.assertRaises(HTTPError, session.patch, "url")

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.patch')
    def test_patch__raises_http_error_if_login_url_redirect_detected(self, mock_patch, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url/login/?goto"
        response.is_redirect = False
        mock_patch.return_value = response
        self.assertRaises(HTTPError, session.patch, "url")

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils.lib.external_session.ExternalSession.update_kwargs_with_verify_option', return_value={})
    @patch('enmutils.lib.external_session.Session.patch')
    def test_patch__raises_http_error_if_redirect_detected(self, mock_patch, *_):
        session = ExternalSession(url="test")
        response = Mock(status_code=200, text="Error")
        response.url = "url"
        response.is_redirect = True
        mock_patch.return_value = response
        self.assertRaises(HTTPError, session.patch, "url")

    def test_update_kwargs_with_verify_option__adds_verify(self):
        session = ExternalSession(url="test")
        self.assertEqual(False, session.update_kwargs_with_verify_option({}).get('verify'))
        self.assertEqual(False, session.update_kwargs_with_verify_option({'verify': False}).get('verify'))


class UsernameAndPasswordUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.external_session.log.logger.debug')
    def test_authenticate__success(self, mock_debug):
        auth = UsernameAndPassword("user", "pass")
        response = Mock(status_code=302)
        session = Mock()
        session.url.return_value = "test"
        session.cookies = {AUTH_COOKIE_KEY: "key"}
        session.post.return_value = response
        auth.authenticate(session)
        self.assertEqual(session.post.call_count, 1)
        mock_debug.assert_called_with('Session successfully opened towards test and user user is authenticated')
        self.assertEqual(None, auth._password)

    @patch('time.sleep')
    def test_authenticate__raises_enm_application_error_if_no_cookie(self, _):
        auth = UsernameAndPassword("user", "pass")
        response = Mock(status_code=302)
        session = Mock()
        session.url.return_value = "test"
        session.cookies = {"cookie": "key"}
        session.post.return_value = response
        self.assertRaises(EnmApplicationError, auth.authenticate, session)

    @patch('enmutils.lib.external_session.is_password_change_redirect', return_value="message")
    @patch('time.sleep')
    def test_authenticate__raises_http_error_if_password_change_or_password_expire_warning(self, *_):
        auth = UsernameAndPassword("user", "pass")
        response = Mock(status_code=200)
        session = Mock()
        session.url.return_value = "test"
        session.post.return_value = response
        self.assertRaises(HTTPError, auth.authenticate, session)

    @patch('enmutils.lib.external_session.is_password_change_redirect', return_value=None)
    @patch('time.sleep')
    def test_authenticate__raises_http_error(self, *_):
        auth = UsernameAndPassword("user", "pass")
        response = Mock(status_code=200)
        response.raise_for_status.side_effect = HTTPError("Error")
        session = Mock()
        session.url.return_value = "test"
        session.post.return_value = response
        self.assertRaises(HTTPError, auth.authenticate, session)

    @patch('time.sleep')
    @patch('enmutils.lib.external_session.log.logger.debug')
    def test_authenticate__timeout_from_post_operation_raises_connectionerror(self, mock_debug, *_):
        auth = UsernameAndPassword("user", "pass")
        session = Mock()
        session.url.return_value = "test"
        session.post.side_effect = Timeout("Connection timed-out")

        with self.assertRaises(ConnectionError) as e:
            auth.authenticate(session)
        self.assertEqual(e.exception.message, "Connection timed-out")
        session.post.assert_called_with("test/login", data={"IDToken1": "user", "IDToken2": "pass"},
                                        allow_redirects=False, timeout=AUTHENTICATION_TIMEOUT)
        self.assertTrue(call("POST operation resulted in exception: Connection timed-out") in mock_debug.mock_calls)
        self.assertEqual(session.post.call_count, 4)
        self.assertEqual(mock_debug.call_count, 5)

    @patch('enmutils.lib.external_session.log.logger.debug')
    def test_logout__success(self, mock_debug):
        auth = UsernameAndPassword("user", "pass")
        session = Mock()
        session.url.return_value = "test"
        auth.logout(session)
        self.assertEqual(1, session.get.call_count)
        mock_debug.assert_called_with("Session closed successfully")

    @patch('enmutils.lib.external_session.json')
    def test_is_password_change_redirect__success_password_change(self, mock_json):
        mock_json.loads.return_value = {"code": "PASSWORD_RESET"}
        expected = 'Invalid login, password change required for user test_user. Please change it via ENM login page'
        self.assertEqual(expected, is_password_change_redirect("text", "test_user"))

    @patch('enmutils.lib.external_session.json')
    def test_is_password_change_redirect__success_password_expire_warning(self, mock_json):
        mock_json.loads.return_value = {"code": "PASSWORD_EXPIRE"}
        expected = 'ENM is requesting a password change - disable password ageing'
        self.assertEqual(expected, is_password_change_redirect("text", "test_user"))

    @patch('enmutils.lib.external_session.json')
    def test_is_password_change_redirect__false(self, mock_json):
        mock_json.loads.return_value = {"code": "SUCCESS"}
        self.assertFalse(is_password_change_redirect("text", "test_user"))

    @patch('enmutils.lib.external_session.json')
    def test_is_password_change_redirect__value_error(self, mock_json):
        mock_json.loads.side_effect = ValueError("Error")
        self.assertFalse(is_password_change_redirect("text", "test_user"))

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

if __name__ == "__main__":
    unittest2.main(verbosity=2)
