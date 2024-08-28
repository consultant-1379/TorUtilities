# ********************************************************************
# Name    : External Session
# Summary : Provides ENM authentication and POST/GET functionality.
# ********************************************************************

import json
import time
from threading import Lock

import requests
from requests import Session, HTTPError, ConnectionError
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib import log

requests.packages.urllib3.disable_warnings()

AUTH_COOKIE_KEY = 'iPlanetDirectoryPro'
_RETRY_ERROR_CODES = (400, 404, 405, 406, 415, 501, 502, 503, 504)
AUTHENTICATION_TIMEOUT = 120  # secs


class ExternalSession(Session):

    # Requests error message
    _ERROR_BAD_STATUS_LINE = '(\'Connection aborted.\', BadStatusLine(\"\'\'\",))'

    def __init__(self, url=None):
        """
        Session that uses the ENM login / logout endpoints to authenticate

        :param url: URL of the ENM deployment to connect to
        :type url: str
        """
        super(ExternalSession, self).__init__()
        self._url = url
        self._request_lock = Lock()
        self._authenticator = None

    def url(self):
        return self._url

    def open_session(self, authenticator):
        """
        Open the authenticator session
        """
        self._authenticator = authenticator
        if authenticator:
            authenticator.authenticate(self)

    def close_session(self, username=None, password=None):
        """
        Close the authenticator session

        :param username: Username to logout of the server
        :type username: str
        :param password: Password to be used to logout the user
        :type password: str
        """
        log.logger.debug('Closing session')
        if self._authenticator:
            self._authenticator.logout(self)
        elif username and password:
            self._authenticator = UsernameAndPassword(username, password)
            self._authenticator.logout(self)
        self.cookies.clear_session_cookies()
        self.close()
        log.logger.debug('Session is closed')

    def authenticator(self):
        """
        Returns the Authenticator instance

        :return: Authenticator instance which will be used for session management
        :rtype: `UsernameAndPassword`
        """
        return self._authenticator

    def post(self, url, data=None, json=None, **kwargs):
        """
        Sends a POST request.

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :type data: dict || bytes || object
        :param json: (optional) json to send in the body of the :class:`Request`.
        :type json: dict
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :raises HTTPError: raised if the POST request fails

        :return: `Response` object
        :rtype: requests.Response
        """
        kwargs = self.update_kwargs_with_verify_option(kwargs)
        kwargs.setdefault('allow_redirects', False)
        with self._request_lock:
            response = super(ExternalSession, self).post(url, data=data, json=json, **kwargs)
            if str(response) == self._ERROR_BAD_STATUS_LINE or response.status_code in _RETRY_ERROR_CODES:
                user_message = build_user_message(response)
                log.logger.debug("POST request to [{0}] has failed,\nresponse.status_code\t{1}, "
                                 "response.reason\t{2}, Message:\t{3}".format(url, response.status_code,
                                                                              response.reason, user_message))
                raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}], "
                                "Message: [{2}]".format(response.status_code, response.reason, user_message),
                                response=response)
            log.logger.debug("Completed POST request to [{0}]".format(url))
            return response

    def get(self, url, **kwargs):
        """
        Sends a GET request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :raises HTTPError: raised if the GET request fails

        :return: `Response` object
        :rtype: requests.Response
        """
        kwargs = self.update_kwargs_with_verify_option(kwargs)
        response = super(ExternalSession, self).get(url, **kwargs)
        if ("login/?goto" in response.url or response.is_redirect) and not kwargs.get('allow_redirects'):
            response.status_code = 302
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}]"
                            .format(response.status_code, response.reason), response=response)
        if str(response) == self._ERROR_BAD_STATUS_LINE or response.status_code in _RETRY_ERROR_CODES:
            user_message = build_user_message(response)
            log.logger.debug("GET request to [{0}] has failed,\nresponse.status_code\t{1}, "
                             "response.reason\t{2}, Message:\t{3}".format(url, response.status_code, response.reason,
                                                                          user_message))
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}], Message: [{2}]"
                            .format(response.status_code, response.reason, user_message), response=response)
        log.logger.debug("Completed GET request to [{0}]".format(url))
        return response

    def put(self, url, data=None, **kwargs):
        """
        Sends a PUT request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :type data: Dictionary, bytes, or file-like object
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :raises HTTPError: raised if the PUT request fails

        :return: `Response` object
        :rtype: requests.Response
        """
        kwargs = self.update_kwargs_with_verify_option(kwargs)
        response = super(ExternalSession, self).put(url, data, **kwargs)
        if ("login/?goto" in response.url or response.is_redirect) and not kwargs.get('allow_redirects'):
            response.status_code = 302
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}]"
                            .format(response.status_code, response.reason), response=response)
        if str(response) == self._ERROR_BAD_STATUS_LINE or response.status_code in _RETRY_ERROR_CODES:
            user_message = build_user_message(response)
            log.logger.debug("PUT request to [{0}] has failed,\nresponse.status_code\t{1}, response.reason\t{2}, "
                             "Message: {3}".format(url, response.status_code, response.reason, user_message))

            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}], Message: [{2}]"
                            .format(response.status_code, response.reason, user_message), response=response)
        log.logger.debug("Completed PUT request to [{0}]".format(url))
        return response

    def delete(self, url, **kwargs):
        """
        Sends a DELETE request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param kwargs: Dictionary of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :raises HTTPError: raised if the DELETE request fails

        :return: `Response` object
        :rtype: requests.Response
        """
        kwargs = self.update_kwargs_with_verify_option(kwargs)
        response = super(ExternalSession, self).delete(url, **kwargs)
        if ("login/?goto" in response.url or response.is_redirect) and not kwargs.get('allow_redirects'):
            response.status_code = 302
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}]"
                            .format(response.status_code, response.reason), response=response)
        if str(response) == self._ERROR_BAD_STATUS_LINE or response.status_code in _RETRY_ERROR_CODES:
            user_message = (json.loads(response.text).get('userMessage') if
                            response.text.startswith('{') else 'Not Available')
            log.logger.debug(
                "DELETE request to [{0}] has failed,\nresponse.status_code\t{1}, response.reason\t{2}, "
                "Message: {3}".format(url, response.status_code, response.reason, user_message))
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}], Message: [{2}]"
                            .format(response.status_code, response.reason, user_message), response=response)
        log.logger.debug("Completed DELETE request to [{0}]".format(url))
        return response

    def patch(self, url, data=None, json=None, **kwargs):
        """
        Sends a PATCH request.

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :type data: dict || bytes || object
        :param json: (optional) json to send in the body of the :class:`Request`.
        :type json: dict
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :raises HTTPError: raised if the PATCH request fails

        :return: `Response` object
        :rtype: requests.Response
        """
        kwargs = self.update_kwargs_with_verify_option(kwargs)
        response = super(ExternalSession, self).patch(url, data=data, json=json, **kwargs)
        if ("login/?goto" in response.url or response.is_redirect) and not kwargs.get('allow_redirects'):
            response.status_code = 302
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}]"
                            .format(response.status_code, response.reason), response=response)
        if str(response) == self._ERROR_BAD_STATUS_LINE or response.status_code in _RETRY_ERROR_CODES:
            log.logger.debug("PATCH request to [{0}] has failed,\nResponse{3}\tresponse.status_code\t{1}, "
                             "response.reason\t{2}".format(url, response.status_code, response.reason,
                                                           str(response)))
            raise HTTPError("Failed to make request, status code:: [{0}] Reason:: [{1}]"
                            .format(response.status_code, response.reason), response=response)
        log.logger.debug("Completed PATCH request to [{0}]".format(url))
        return response

    @staticmethod
    def update_kwargs_with_verify_option(kwargs):
        """
        Update the dictionary of kwargs to be supplied the REST request - SSL certificate verify value

        :param kwargs: Dictionary of kwargs to be supplied the REST request
        :type kwargs: dict

        :return: Updated dictionary of kwargs to be supplied the REST request
        :rtype: dict
        """

        if 'verify' not in kwargs:
            kwargs['verify'] = False
        return kwargs


class UsernameAndPassword(object):

    def __init__(self, username, password):
        """
        Init method

        :param username: Username to authenticate on the server
        :type username: str
        :param password: Password to be used to authenticate the user
        :type password: str
        """
        super(UsernameAndPassword, self).__init__()
        self._username = username
        self._password = password

    def authenticate(self, session):
        """
        Authenticate the user session

        :param session: Session instance to be authenticated
        :type session: `ExternalSession`

        :raises HTTPError: raised if the credentials are invalid or a user password change is detected
        :raises EnmApplicationError: raised if the credentials are invalid or a user password change is detected
        :raises ConnectionError: raised if the ENM connectivity problems occurred
        """
        max_attempts = 3
        wait_time = 5

        log.logger.debug('Authenticating user [{0}]'.format(self._username))
        kwargs = {"allow_redirects": False, "timeout": AUTHENTICATION_TIMEOUT}
        for i in range(max_attempts + 1):
            try:
                try:
                    auth_response = session.post(''.join((session.url(), '/login')),
                                                 data={'IDToken1': self._username, 'IDToken2': self._password}, **kwargs)
                except Exception as e:
                    log.logger.debug("POST operation resulted in exception: {0}".format(str(e)))
                    raise ConnectionError(str(e))

                if auth_response.status_code == 302:
                    if AUTH_COOKIE_KEY not in session.cookies.keys():
                        raise EnmApplicationError('Invalid login, credentials are invalid for user {0}'.format(self._username))

                else:
                    log.logger.debug(
                        'Login server response is {0}{1}'.format(str(auth_response.status_code), auth_response.text))
                    password_redirect = is_password_change_redirect(auth_response.text, self._username)
                    if auth_response.status_code == 200 and password_redirect:
                        # Redirect detected
                        raise HTTPError(password_redirect, response=auth_response)
                    auth_response.raise_for_status()
                log.logger.debug('Session successfully opened towards {0} and user {1} is authenticated'.format(session.url(),
                                                                                                                self._username))
                self._password = None
                return
            except (ConnectionError, EnmApplicationError, HTTPError) as e:
                if i < max_attempts:
                    time.sleep(wait_time)
                    continue
                raise

    @staticmethod
    def logout(session):
        """
        Logout function

        :param session: Session instance to be closed
        :type session: `ExternalSession`
        """
        kwargs = {"allow_redirects": True}
        session.get(''.join((session.url(), '/logout')), **kwargs)
        log.logger.debug("Session closed successfully")


def is_password_change_redirect(text, user):
    """
    Detects if redirect is to change user password details

    :param user: user tyring to login
    :type user: str
    :param text: String object to be loaded from json into python dict
    :type text: str

    :return: Boolean indicating if redirect is to change user password details
    :rtype: bool
    """
    try:
        if json.loads(text).get("code") == "PASSWORD_RESET":
            return ('Invalid login, password change required for user {0}. '
                    'Please change it via ENM login page'.format(user))
        elif json.loads(text).get("code") == "PASSWORD_EXPIRE":
            return 'ENM is requesting a password change - disable password ageing'
    except ValueError:
        pass


def build_user_message(response):
    """
    Determines the content type of a response object and sets the user message appropriately

    :param response: The HTTPResponse object to query for a userMessage
    :type response: `requests.Response`

    :return: Message determined from the response object
    :rtype: str
    """
    content_type = None
    for header_field in response.headers.keys():
        if header_field.lower() == "content-type":
            content_type = header_field

    if content_type and response.headers.get(content_type) == "application/json":
        try:
            message = response.json()
            if "userMessage" in message:
                message = message["userMessage"]
            else:
                message = json.dumps(message)
        except (AttributeError, ValueError) as e:
            message = str(e)
    else:
        message = response.text
    return message
