# ********************************************************************
# Name    : ENM User 2
# Summary : Contains multiple classes related to ENM User creation.
# ********************************************************************

import getpass
import json
import os
import pkgutil
import re
import time
from collections import defaultdict
from random import randint
from urlparse import urljoin, urlparse

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException
from requests.models import Request, Response
import enmscripting
from enmscripting.exceptions import SessionTimeoutException

import cache
import config
import exception
import filesystem
import log
import persistence
import mutexer
import shell

from enmutils.lib.persistence import persistable
from headers import DELETE_SECURITY_REQUEST, SECURITY_REQUEST_HEADERS
from .exceptions import (EnmApplicationError, EnvironError, NoOuputFromScriptEngineResponseError, PasswordDisableError,
                         RolesAssignmentError, SessionNotEstablishedException)
from .external_session import ExternalSession, UsernameAndPassword, AUTH_COOKIE_KEY

SESSION_TIMEOUTS = ['loginUsername', '401 Authorization Required', 'Session timeout error', 'aborted', 'Pool is closed',
                    'Invalid login', 'Authentication failed', '(\'Connection aborted.\', BadStatusLine(\"\'\'\",))']
ADMINISTRATOR_IDENTIFIER = 'administrator'
WORKLOAD_ADMIN_SESSION_KEY = 'workload_admin_session'
ADMINISTRATOR_SESSION_KEY = 'administrator_session'
USER_IDENTIFIER = '{username}'
SSO_URL = 'login'
INTERNAL_ID = 'enmutils_int'
INITIAL_PROMPT = "\nPlease enter the credentials of the ENM account to use"
USERNAME_PROMPT = "Username: "
PASSWORD_PROMPT = "Password: "
FILES_DIR = '/tmp/enmutils'
HAPROXY_OFFLINE_KEY = "ha-proxy-offline-value"
HAPROXY_DOWNTIME_SECS = 45


class NoStoredPasswordError(Exception):
    pass


@persistable
class User(object):

    BASE_URL = '/oss/idm/usermanagement/users'
    USER_URL = '/oss/idm/usermanagement/users/{username}/'
    MODIFY_PRIVELEGES_URL = "/oss/idm/usermanagement/modifyprivileges"
    FORCE_PASSWORD_CHANGE_URL = urljoin(USER_URL, 'forcepasswordchange')
    CHANGE_PASSWORD_URL = urljoin(USER_URL, 'password')
    BASE_SESSION_URL = "/oss/sso/utilities/users/"
    GET_USER_PRIVILEGES_URL = "/oss/idm/usermanagement/users/{0}/privileges"

    _PERSISTENCE_KEY = '{username}_session'
    HAPROXY_DOWNTIME_SECS = HAPROXY_DOWNTIME_SECS

    def __init__(self, username, password=None, first_name=None, last_name=None, roles=(), **kwargs):
        """
        Load user constructor.

        :param username: The user's username
        :type username: str
        :param password: The user's password
        :type password: str
        :param first_name: The user's first name
        :type first_name: str
        :param last_name: The user's last name (str)
        :type last_name: str
        :param roles: The openIDM security roles to which the user will be assigned (list)
        :type roles: list
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
                                    - The user's email (str)
                                    - The user's description (str)
                                    - If a session should be established on ENM for the created username (bool)
                                    - Attaches password to a Session object for this ENM user so sessions can be
                                      re-established when they expire (bool)
                                    - Toggles whether or not to disable password reset after logging into ENM (bool)
                                    - Ignore all requests exception except MissingSchema, InvalidSchema, InvalidURL
                                      and logs them to this instance
                                    - Flag to indicate if the user to be persisted is the default admin user
                                    - bool indicating if the user instance should persist itself in memory.
                                    - status for user e.g. enabled or disabled
        :type kwargs: dict
        """

        self.username = username
        self.password = password

        self.roles = set(EnmRole(role) if isinstance(role, basestring) else role for role in roles)

        self.first_name = first_name
        self.last_name = last_name

        if not self.first_name:
            self.first_name = username

        if not self.last_name:
            self.last_name = username

        self.email = kwargs.pop('email', "{0}@{1}".format(self.username, 'ericsson.com'))
        self.description = kwargs.pop('description', "")
        self.password_reset_disabled = kwargs.pop('password_reset_disabled', True)
        self.establish_session = kwargs.pop('establish_session', True)
        self.keep_password = kwargs.pop('keep_password', False)
        self.safe_request = kwargs.pop('safe_request', False)
        self.persist = kwargs.pop('persist', True)
        self.status = kwargs.pop('status', 'enabled')

        self.user_type = kwargs.pop('user_type', "enmUser")
        self.temp_password = kwargs.pop('temp_password', 'TempPassw0rd')
        self.nodes = kwargs.pop('nodes', [])
        self.enm_session = None
        self._enmscripting_session = None
        self._session_key = kwargs.pop('_session_key', None)
        self.ui_response_info = kwargs.pop('ui_response_info', defaultdict(dict))
        self._persistence_key = kwargs.pop('_persistence_key', User._PERSISTENCE_KEY.format(
            username=self.get_username_of_admin_user() if kwargs.pop('is_default_admin', False) else username))
        self.workspace_id = "workspace_{}".format(randint(1000000000000, 9999999999999))

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            exception.process_exception()

        self.delete()

    def has_role_name(self, role):
        """
        Checks if this user instance has the specified role.

        :type role: string
        :param role: The openIDM role to Checks
        :rtype: boolean
        :return: True if the user has the role in his or her list of roles
        """
        return role in set(role.name for role in self.roles)

    def get_enm_user_information(self):
        """
        Gets the user information from ENM

        :return: The user information or None
        :rtype: dict
        :raises RuntimeError: if there is no session found
        """

        user_dict = None
        session = self.session or get_admin_user().session
        if not session:
            raise RuntimeError('No session found to make the get user request')
        headers_dict = SECURITY_REQUEST_HEADERS
        response = self.get(self.USER_URL.format(username=self.username), headers=headers_dict)

        if response.ok:

            log.logger.debug("Successfully fetched user information '{0}'. response = '{1}'"
                             .format(self.username, response.text))
            user_dict = json.loads(response.text)

        return user_dict

    def is_session_established(self, url=None):
        """
        Checks if this user instance exists in ENM

        :type url: string
        :param url: URL of the ENM server to check session against
        :rtype: boolean
        :return: True if the user exists in ENM
        :raises SessionNotEstablishedException: if http and connection error occurs
        """

        try:
            self.open_session(url=url)
            if self.session and self.get_enm_user_information():
                log.logger.debug("Verified that user '{0}' exists".format(self.username))
                return True
        except NoStoredPasswordError:
            self.remove_session()
        except (HTTPError, ConnectionError) as e:
            raise SessionNotEstablishedException("Unable to establish session for user {0}. Exception: {1}"
                                                 .format(self.username, str(e)))

        return False

    def open_session(self, reestablish=False, url=None):
        """
        Open the session to ENM, it will try to reuse the existing cookie if there is one,
        otherwise it will actually try to login to the ENM application given the login
        credentials.

        :param reestablish: bool that forces the session to be reestablished or not
        :type reestablish: bool
        :param url: FQDN Apache URL of the ENM system the session will be opened against.
        :type url: str or None

        :raises NoStoredPasswordError: if reestablish and keep_password is False
        """
        log.logger.debug("Opening session towards ENM")
        url = url or cache.get_apache_url()
        log.logger.debug('Using host %s to make connections' % url)
        session = ExternalSession(url)
        login = True
        if reestablish:
            log.logger.debug('Trying to RE-ESTABLISH a session to ENM for user "%s"' % self.username)
            if not self.keep_password:
                raise NoStoredPasswordError(
                    'Cannot RE-ESTABLISH session because we don\'t have password stored for user %s' % self.username)
        else:
            if self._session_key:
                log.logger.debug('Existing session cookie found for user "%s"' % self.username)
                session.cookies[AUTH_COOKIE_KEY] = self._session_key
                login = False
        if login:
            self.login(session)
        self.enm_session = session

    def login(self, session):
        """
        Login to ENM

        :param session: Session to be opened in ENM
        :type session: `external_session.ExternalSession` instance

        :raises Exception: raised if the request fails
        """
        try:
            log.logger.debug('Trying to login to ENM for user {}'.format(self.username))
            session.open_session(UsernameAndPassword(
                self.username, config.get_encoded_password_and_decode(self.username, self.password)))
            self._session_key = session.cookies[AUTH_COOKIE_KEY]
            log.logger.debug('User {} successfully logged in ENM'.format(self.username))
            # Only persist the administrator session if the enmutils internal package is installed
            if self.persist and pkgutil.get_loader(INTERNAL_ID):
                with mutexer.mutex("{0}-session-key".format(self._persistence_key), persisted=True, log_output=True):
                    persistence.set(self._persistence_key, self, -1)
        except Exception as e:
            if "401" in str(e):
                with mutexer.mutex("{0}-session-key".format(self._persistence_key), persisted=True, log_output=True):
                    persistence.remove(self._persistence_key)
                log.logger.debug("User not authorised, please ensure user is created correctly and expected "
                                 "credentials are valid.")
            raise

    def open_enmscripting_session(self, url):
        """
        Open session using the ENMScripting library

        :raises SessionTimeoutException: raised if ENMScripting fails to login

        :param url: Valid ENM url
        :type url: str
        """
        log.logger.debug('Attempting to open enm scripting session for {0}'.format(self.username))
        try:
            self._enmscripting_session = enmscripting.open(
                url, self.username, config.get_encoded_password_and_decode(self.username, self.password))
            log.logger.debug("Session opened successfully")
        except (SessionTimeoutException, ValueError) as e:
            log.logger.debug("Exception occurred while opening session: {0}".format(str(e)))
            raise SessionTimeoutException(str(e))

    def get_username_of_admin_user(self):
        """
        Gets the administrator username.

        :rtype:     username
        :return:    administrator username
        """
        username = USER_IDENTIFIER.format(username=self.username)
        return username

    @property
    def session(self):
        return self.enm_session or None

    def get_enmscripting_session(self):
        """
        Retrieve the available enm scripting session object

        :return: EnmSession instance from the enm scripting library
        :rtype: `ExternalSession`
        """
        return self._enmscripting_session

    @classmethod
    def get_usernames(cls, user=None):
        """
        Gets a list of all usernames for users created on ENM

        :type user: enm_user_2.User
        :param user: user instance for issuing request
        :rtype: list
        :return: True if the response returned a 200 OK
        """
        user = user or get_admin_user()
        response = user.get(cls.BASE_URL, headers=SECURITY_REQUEST_HEADERS)
        response.raise_for_status()
        return [user_dict["username"] for user_dict in response.json()]

    def remove_session(self, username=None):
        """
        Removes the session for this user from ENM

        :param username: Username to be used to close session
        :type username: str
        """
        username = username if username else self.username
        if self.session:
            self.session.close_session(username=username, password=self.password)
            log.logger.debug('Successfully removed user session "{0}"'.format(username))
        self.enm_session = None
        persistence.remove(self._persistence_key)

    def _execute_cmd(self, cmd, **kwargs):
        """
        Executes the given command on the enm's script engine

        :param cmd: command to run
        :type cmd: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :raises SessionTimeoutException: raised if the session has timed out in ENM
        :raises Exception: raised if the request fails but not due to session timeout

        :return: Response object returned by the command execution
        :rtype: `enmscripting.Response` object
        """
        max_attempts = 3
        wait_time = 5
        on_terminal = kwargs.pop('on_terminal')
        timeout_seconds = kwargs.pop('timeout_seconds') if 'timeout_seconds' in kwargs else 600
        for i in range(max_attempts + 1):
            try:
                if 'file' in cmd:
                    log.logger.debug("File to be used :{0}".format(kwargs.get('file')))
                log.logger.debug('Attempting to execute command: {0}'.format(cmd))
                try:
                    if hasattr(self, "_enmscripting_session") and self.session:
                        self.open_enmscripting_session(self.session.url())
                    log.logger.debug("Executing CM CLI command on ENM")
                    if on_terminal:
                        response = self.get_enmscripting_session().terminal().execute(cmd, timeout_seconds=timeout_seconds,
                                                                                      **kwargs)
                    else:
                        response = self.get_enmscripting_session().command().execute(cmd, timeout_seconds=timeout_seconds,
                                                                                     **kwargs)
                    log.logger.debug("Command execution on ENM complete")
                    return response
                except SessionTimeoutException as e:
                    log.logger.debug("Redirected to ENM login. SessionTimeoutException received from enmscripting - "
                                     "Therefore we will try to login again. {0}".format(str(e)))
                    self.open_enmscripting_session(self.session.url())
                    raise
                except Exception as e:
                    if "Pool is closed" in e.message:
                        log.logger.error("Closed Pool Error received from enmscripting. Re-Executing ScriptEngine command {0}"
                                         .format(cmd))
                        self.open_enmscripting_session(self.session.url())
                        raise SessionTimeoutException(str(e))
                    raise
            except SessionTimeoutException as e:
                if i < max_attempts:
                    time.sleep(wait_time)
                    continue
                raise

    def enm_execute(self, command, on_terminal=True, file_in=None, timeout_seconds=None, outfile=None):
        """
        Executes the given command on the enm's script engine

        :param command: command to run
        :type command: str
        :param on_terminal: bool to indicate if to run command using enmscripting terminal
        :type on_terminal: bool
        :param file_in: path to the file to use in the enm command
        :type file_in: str
        :param timeout_seconds: number of seconds to wait for command to respond
        :type timeout_seconds: int
        :param outfile: File path to save any attached file object to if available
        :type outfile: str

        :raises NoOuputFromScriptEngineResponseError: raised if there is no response output
        :raises OSError: if the file doesn't exist in the path
        :raises EnmApplicationError: raised if error is received from enmscripting that is not a ClosedPoolError

        :return: Response object returned by the command execution
        :rtype: `enmscripting.Response` object
        """

        if self.enm_session is None:
            self.open_session()

        if file_in and not os.path.isfile(file_in):
            raise OSError('File "%s" does not exist' % file_in)

        kwargs = {'on_terminal': on_terminal}

        if timeout_seconds:
            kwargs['timeout_seconds'] = int(timeout_seconds)

        file_obj = None
        if file_in:
            log.logger.debug("File provided for job is : {0}".format(file_in))
            file_obj = kwargs['file'] = open(file_in, 'rb')
        mod_cmd = None
        if 'password' in command:
            mod_cmd = re.sub(r"password\s+\S+", "password ********", command)
        try:
            response = self._execute_cmd(command, **kwargs)
            if outfile and response.has_files():
                for enm_file in response.files():
                    outfile_path = outfile or os.path.join(FILES_DIR, enm_file.get_name())
                    enm_file.download(outfile_path)
                log.logger.info('Downloaded file {0}'.format(outfile))
        except Exception as e:
            log.logger.debug("Failed while executing ScriptEngine command '{0}' with file '{1}' "
                             .format(mod_cmd[:1000] if mod_cmd else command[:1000], file_in))
            raise EnmApplicationError(e)
        finally:
            self._close_file_and_close_session(file_obj)

        response.command = command
        if not response.is_command_result_available():
            raise NoOuputFromScriptEngineResponseError("No output to parse from ScriptEngineCommand {0}"
                                                       "".format(command[:1000]), response=response)

        return response

    def _close_file_and_close_session(self, file_obj):
        """
        If there is a file object, close it. Close the user session
        :param file_obj: file object
        :type file_obj: BinaryIO
        """
        if file_obj:
            file_obj.close()
        if config.has_prop('close_session') and config.get_prop('close_session') is True and self.session:
            self.session.close_session()
            log.logger.debug('Successfully closed user session "{0}"'.format(self.username))
        try:
            self.enm_session._session.close()
        except AttributeError:
            log.logger.debug('Closing enm scripting session for {0}'.format(self.username))
            session = self.get_enmscripting_session()
            if session:
                try:
                    enmscripting.close(session)
                except Exception as e:
                    msg = 'The enm scripting session has already been closed for {0}'.format(self.username)
                    error_message = msg if "Pool is closed" in e.message else e.message
                    log.logger.debug(error_message)
                else:
                    log.logger.debug('Successfully closed enm scripting session for {0}'.format(self.username))

    def _log_for_status(self, response, ignore_status_lst=None):
        """Adds entry to failed_requests if status code is not valid in response

        :param response: `requests.models.Response` to log
        :type response: requests.models.Response
        :param ignore_status_lst: bool indicating if we need to append this failed request to user
        :type ignore_status_lst: bool
        """

        # We will always want to ignore 401s as these AuthorizationErrors are followed by the user trying to reestablish
        ignore_status_lst = ignore_status_lst or []
        ignore_status_lst.append(401)

        try:
            response.raise_for_status()
        except RequestException as e:
            # We are suppressing HTML Error message for code 401
            if e.response.status_code == 401:
                log.logger.debug('%s request to "%s" failed with status code %s. ENM session lost or failed '
                                 'to open.' % (e.response.request.method, e.response.url, e.response.status_code))
            else:
                log.logger.debug('%s request to "%s" failed with status code %s and response %s' % (
                    e.response.request.method, e.response.url, e.response.status_code, e.response.text))

        else:
            log.logger.debug('%s request to "%s" was successful' % (
                response.request.method, response.request.url))

        # How should we handle failed requests with status_code in ignore_status_lst?
        # I've chosen to ignore them for now as if the requests were never made but am open to suggestions
        if self.safe_request and response.status_code not in ignore_status_lst:
            self._process_safe_request(response)

    def _process_safe_request(self, response):
        """
        Adds information from a response to the ui_response_info dict for aggregation in the profile class

        :type response: requests.models.Response
        :param response: response object to process for ui_profiles
        """

        if response.request.url.split("/")[-1].isdigit():
            response.request.url = "/".join(response.request.url.split("/")[:-1] + ["<id>"])
        elif bool(re.search(r'\d', response.request.url)):
            response.request.url = re.sub(r"\d+", "[NUM]", response.request.url)
        request_key = (response.request.method, response.request.url)
        if request_key not in self.ui_response_info:
            self.ui_response_info[request_key][True] = 0
            self.ui_response_info[request_key][False] = 0

        self.ui_response_info[request_key][response.ok] += 1

        if not response.ok:
            if "ERRORS" not in self.ui_response_info[request_key]:
                self.ui_response_info[request_key]["ERRORS"] = {response.status_code: response}
            elif response.status_code not in self.ui_response_info[request_key]["ERRORS"]:
                self.ui_response_info[request_key]["ERRORS"][response.status_code] = response

    def _make_request(self, method, url, timeout=120, **kwargs):
        """
        Sends a http request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param method: HTTP method
        :type method: str
        :param timeout: timeout value if there is no response for the sent request
        :type timeout: int
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: `Response` object
        :rtype: requests.Response
        :raises RequestException: if there is exception in response
        :raises e: RequestException If there is an exception in reponse
        """
        ignore_status_lst = kwargs.pop('ignore_status_lst', None)
        try:
            kwargs.setdefault('timeout', timeout)
            operation = getattr(self.session, method.lower())
            response = operation(url, **kwargs)
            if response is None:
                raise RequestException("There is no response for {0} method.".format(method))
        except RequestException as e:
            if not self.safe_request:
                raise e
            response = e.response if e.response else _get_failed_response(method, url, e)

        self._log_for_status(response, ignore_status_lst=ignore_status_lst)
        return response

    def request(self, method, url, profile_name=None, **kwargs):
        """
        Sends an HTTP request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param method: HTTP method
        :type method: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :rtype: requests.Response
        :return: `Response` object

        :raises HTTPError: if the ENM request fails
        :raises ConnectionError: if the connection to ENM is aborted
        """
        if not self.session:
            self.open_session()
        kwargs.setdefault('verify', False)
        retry_msg = ("WARNING: Session lost on application side. Removing current session from persistence and trying "
                     "to re-establish the session.")
        if not urlparse(url).netloc:
            url = urljoin(self.session.url(), "/{0}".format(url) if not url.startswith("/") and not self.session.url().endswith('/') else url)
        response = self.request_response(method, url, profile_name, retry_msg, **kwargs)
        return response

    def request_response(self, method, url, profile_name, retry_msg, **kwargs):
        """
        Method to send an HTTP request and returns the response

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param method: HTTP method
        :type method: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param retry_msg: Retry message
        :type retry_msg: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict

        :rtype: requests.Response
        :return: `Response` object

        :raises HTTPError: if the ENM request fails
        :raises ConnectionError: if the connection to ENM is aborted
        """
        try:
            response = self._make_request(method, url, **kwargs)
            if "NETEX_03" in str(profile_name):
                persistence.set("{0}_re_establish".format(profile_name), False, -1)
        except (ConnectionError, HTTPError) as e:
            response = self.validate_error_response(e, retry_msg)
            if response and "DYNAMIC_CRUD" not in str(profile_name):
                self.open_session(reestablish=True)
                response = self._make_request(method, url, **kwargs)
            else:
                log.logger.debug("Not re-establishing session for {0} and error is {1}.".format(profile_name, e))
                error_response = e.response if hasattr(e, "response") else _get_failed_response(method, url, e)
                return error_response
        else:
            if response.status_code in (401, 301, 302, 403, 502, 504) and "DYNAMIC_CRUD" not in str(profile_name):
                log.logger.debug(retry_msg)
                self.open_session(reestablish=True)
                self.netex_new_time(profile_name)
                response = self._make_request(method, url, **kwargs)
        return response

    def netex_new_time(self, profile_name):
        """
        This method checks if its netex_03 profile and set new_time to persistence
        :param profile_name: The profile name for which the execution occurs only for Netex_03 profile.
        :type profile_name: str
        """
        if "NETEX_03" in str(profile_name):
            new_time = time.time()
            persistence.set("{0}_re_establish".format(profile_name), new_time, -1)

    def validate_error_response(self, e, retry_msg):
        """
        validate the api error response

        :param e: exception
        :type e: exception object
        :param retry_msg: message for re-establish the user session, if previous user session expired in enm
        :type retry_msg: str
        :return: retry_request value. True, False
        :rtype: bool

        :raises e: (Exception) if there is exception in response
        """
        retry_request = False
        log.logger.debug("Errors occurred during REST request : {0}".format(e))

        if (("Network is unreachable" in str(e)) or ("Service Unavailable" in str(e))) and not check_haproxy_online():
            log.logger.debug("Sleeping for {0} seconds due to haproxy down time before "
                             "retrying......".format(self.HAPROXY_DOWNTIME_SECS))
            time.sleep(self.HAPROXY_DOWNTIME_SECS)
            retry_request = True

        elif (e.response and (e.response.status_code in (401, 302, 403, 502, 504) or
                              any(x in e.response.text for x in SESSION_TIMEOUTS))):
            log.logger.debug(retry_msg)
            message = build_user_message(e.response)
            log.logger.debug(message)
            retry_request = True
        else:
            raise e

        return retry_request

    def get(self, url, profile_name=None, **kwargs):
        """
        Sends a GET request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: `Response` object
        :rtype: requests.Response
        """
        return self.request('GET', url, profile_name=profile_name, **kwargs)

    def head(self, url, **kwargs):
        """
        Sends a HEAD request.

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: `Response` object
        :rtype: requests.Response
        """
        return self.request('HEAD', url, **kwargs)

    def post(self, url, profile_name=None, data=None, json=None, **kwargs):
        """
        Sends a POST request.

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :type data: dict || bytes || object
        :param json: (optional) json to send in the body of the :class:`Request`.
        :type json: dict
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: `Response` object
        :rtype: requests.Response
        """
        return self.request('POST', url, profile_name=profile_name, data=data, json=json, **kwargs)

    def put(self, url, profile_name=None, data=None, **kwargs):
        """
        Sends a PUT request.

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :type data: dict || bytes || object
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: `Response` object
        :rtype: requests.Response
        """
        return self.request('PUT', url, profile_name=profile_name, data=data, **kwargs)

    def delete_request(self, url, profile_name=None, **kwargs):
        """
        Sends a DELETE request

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: Response` object
        :rtype: requests.Response
        """
        return self.request('DELETE', url, profile_name=profile_name, **kwargs)

    def patch(self, url, profile_name=None, data=None, json=None, **kwargs):
        """
        Sends a PATCH request.

        :param url: URL for the new :class:`Request` object.
        :type url: str
        :param profile_name: Name of the profile
        :type profile_name: str
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :type data: dict || bytes || object
        :param json: (optional) json to send in the body of the :class:`Request`.
        :type json: dict
        :param profile_name: Name of the profile
        :type profile_name: str
        :param kwargs: Diction of keyword arguments to be passed to the function/method when it is invoked
        :type kwargs: dict
        :return: `Response` object
        :rtype: requests.Response
        """
        return self.request('PATCH', url, profile_name=profile_name, data=data, json=json, **kwargs)

    def create(self, create_as=None):
        """
        Creates the user in ENM

        :param create_as: user instance to use for creating the new user.
        :type create_as: enm_user_2.User

        :raises HTTPError: when status_code is not 200 or 201
        :raises RuntimeError: when established is false or password_reset_disabled and verify_credentials
                condition is true
        :raises EnmApplicationError: when user creation post command fails
        """
        create_as = create_as or get_admin_user()

        payload = {
            "username": self.username,
            "password": config.get_encoded_password_and_decode(self.username, self.password),
            "status": self.status,
            "name": self.first_name,
            "surname": self.last_name,
            "email": self.email,
            "description": self.description,
            "passwordResetFlag": not self.password_reset_disabled,
            "privileges": []
        }

        for role in self.roles:
            for target in role.targets:
                payload["privileges"].append({
                    "role": role.name,
                    "targetGroup": target.name
                })

        try:
            response = create_as.post(self.BASE_URL, json=payload, headers=SECURITY_REQUEST_HEADERS)
        except Exception as e:
            raise EnmApplicationError(e)

        if response.status_code not in [200, 201]:
            self.get_http_error_for_failed_user_creation(response)

        log.logger.debug("Successfully created user {0} with role: {1}".format(self.username, ','.join(
            str(role) for role in self.roles)))

        if self.establish_session:
            try:
                self.establish_enm_session()
            except RequestException as e:
                self.delete()
                raise RuntimeError('Maximum retries reached. Cannot establish session for user {0}. '
                                   'Error encountered:: {1}'.format(self.username, str(e)))
        else:
            # If we disabled the password reset for a user we created,
            # we only want to raise a runtime error if we cannot login with that credentials.
            # Need to sleep temporarily to allow user to be created
            time.sleep(2)
            if self.password_reset_disabled and not verify_credentials(self.username, self.password,
                                                                       create_as.session.url()):
                raise RuntimeError(
                    "Unable to login with credentials username: {0} password: {1}".format(self.username, self.password))

    def get_http_error_for_failed_user_creation(self, response):
        """
        Retrieves HTTPError in the event of failed user creation.
        This HTTPError details the failure reason to the end user.

        :param response: HTTPResponse from the failed user creation POST request.
        :type  response: HTTPResponse object

        :raises HTTPError: raises HTTPError detailing failure reason to the end user.
        """
        message = build_user_message(response)
        if "User Profile workload_admin already exists" in message:
            raise HTTPError('An attempt to create the user "{0}" has failed as that user already exists on ENM. '
                            'This is an unexpected situation.'
                            'This user needs to be manually deleted from ENM first before workload '
                            'profiles can be started.'.format(self.username))
        else:
            raise HTTPError(
                'User "{0}" with {1} roles failed to create. Reason "{2}"'.format(self.username, len(self.roles),
                                                                                  message), response=response)

    def establish_enm_session(self):
        """
        Establish a session to ENM

        :raises RequestException: raised if the session cannot be established

        :return: Boolean indicating if the session was opened successfully
        :rtype: bool | NoneType
        """
        # Bug where login invalid credentials exception raised if we don't sleep
        max_attempts = 3
        wait_time = 5
        for i in range(max_attempts + 1):
            try:
                self.open_session()
                return True
            except RequestException as e:
                log.logger.debug('Cannot login with the user {0}, after sleeping for an additional 5 seconds. '
                                 'Trying again... Error Message was {1}'.format(self.username, str(e)))
                if i < max_attempts:
                    time.sleep(wait_time * (i + 1))
                    continue
                raise

    def delete(self, delete_as=None):
        """
        Deletes the user from ENM
        :param delete_as: user instance to use for deleting this user.
        :type delete_as: User.user
        :raises HTTPError: when response is None and response.status_code is greater than 300
        """

        delete_as = delete_as or get_admin_user()

        url = self.USER_URL.format(username=self.username)
        response = None
        try:
            response = delete_as.delete_request(url, headers=DELETE_SECURITY_REQUEST)
        except ValueError as e:
            log.logger.debug(e.message)

        if response and response.status_code >= 300:
            raise HTTPError('Unable to delete user %s. Reason "%s"' % (self.username, response.text), response=response)

        if self.session:
            self.remove_session()
        else:
            persistence.remove(self._persistence_key)

    def assign_to_roles(self, roles=None, assign_as=None):
        """
        Assigns a user to one or many roles

        :param assign_as: user instance to use for assigning roles to this user.
        :type assign_as: enm_user_2.User
        :param roles: List of openIDM roles in which to assign the user to
        :type roles: list
        :raises RolesAssignmentError: if the status code is not 200 or 201
        """

        roles = roles or self.roles
        assign_as = assign_as or get_admin_user()

        log.logger.debug("Assigning user {0} to roles {1}".format(self.username, log.purple_text(roles)))

        payload = [{
            "action": "ADD",
            "user": self.username,
            "targetGroup": "ALL",
            "role": role} for role in roles]

        response = assign_as.put(
            self.MODIFY_PRIVELEGES_URL,
            json=payload, headers=SECURITY_REQUEST_HEADERS,
            verify=False, timeout=60)

        if response.status_code not in [200, 201]:
            log.logger.debug("Unable to assign roles {0} to user {1}".format(roles, self.username))
            log.logger.debug("    Output: {0}".format(response.text))
            raise RolesAssignmentError('Unable to assign roles [{0}] to user {1}. Reason "{2}"'
                                       .format(','.join(role.name for role in roles), self.username, response.text),
                                       response=response)

        log.logger.debug('Successfully assigned roles "%s" to user "%s"' % (','.join(role.name for role in roles),
                                                                            self.username))

    def set_status(self, status, assign_as=None):
        """
        Toggle the status of the user passed in

        :param status: new status for user (string). e.g. enabled or disabled
        :type status: str
        :param assign_as: : user instance to carry out request with (EnmUser)
        :type assign_as: enm_user_2.User
        :raises HTTPError: if status code is not 200 or 201
        """

        assign_as = assign_as or get_admin_user()

        log.logger.debug("Changing status to {0} for user {1}".format(log.purple_text(status), self.username))

        payload = {"username": self.username, "status": status, "name": self.first_name,
                   "surname": self.last_name, "email": self.email}

        response = assign_as.put(self.USER_URL.format(username=self.username),
                                 json=payload, headers=SECURITY_REQUEST_HEADERS)

        if response.status_code not in [200, 201]:
            raise HTTPError('Unable to change status to "%s". Reason "%s"' % (status, response.text), response=response)

        log.logger.debug('Successfully changed status of user "%s" to "%s"' % (self.username, status))

    def _teardown(self):
        self.delete()

    def change_password(self, change_as=None):
        """

        :param change_as: `User` instance
        :type change_as: enm_user_2.User
        :raises PasswordDisableError: if status code is not equal to 204
        """

        change_as = change_as or get_admin_user()

        log.logger.debug('Trying to change password for user %s' % self.username)

        response = change_as.put(
            self.CHANGE_PASSWORD_URL.format(username=self.username),
            json={"oldPassword": self.temp_password, "password": self.password},
            headers=SECURITY_REQUEST_HEADERS)
        if response.status_code != 204:
            raise PasswordDisableError('Cannot change the password for user %s. Reason "%s"' % (self.username, response.text), response=response)

        log.logger.debug('Successfully changed password reset for user %s' % self.username)

    def get_roles(self):
        """
        Gets all the roles assigned to the user

        :return:a set list of user roles
        :rtype: set[EnmRole]
        :raises HTTPError: if response is not ok
        """
        response = self.get(User.GET_USER_PRIVILEGES_URL.format(self.username), headers=SECURITY_REQUEST_HEADERS)
        if not response.ok:
            raise HTTPError('Unable to retrieve user privileges. Reason "%s"' % response.text, response=response)
        role_and_targets = defaultdict(list)
        for role_definition in response.json():
            role_and_targets[role_definition["role"]].append(role_definition["targetGroup"])

        return set([EnmRole(name, targets=targets, user=self.username) for name, targets in role_and_targets.iteritems()])

    def __setstate__(self, state):
        for attr, val in state.iteritems():
            setattr(self, attr, val)
        self.enm_session = None


def get_user_privileges(username, user=None):
    """
    Gets all the privileges assigned to a username

    :type username: str
    :param username: ENM username
    :type user: enm_user_2.User
    :param user: User instance
    :return: a set list of user priviliges
    :rtype: set[EnmRole]
    :raises HTTPError: if response is not ok
    """
    user = user or get_admin_user()
    response = user.get(User.GET_USER_PRIVILEGES_URL.format(username), headers=SECURITY_REQUEST_HEADERS)
    if not response.ok:
        raise HTTPError('Unable to retrieve user privileges. Reason "%s"' % response.text, response=response)

    role_and_targets = defaultdict(list)
    for role_definition in response.json():
        role_and_targets[role_definition["role"]].append(role_definition["targetGroup"])

    return set([EnmRole(name, targets=targets) for name, targets in role_and_targets.iteritems()])


def get_all_sessions():
    """
    Gets all the users currently logged into ENM

    :return: json dictionary {user_name: number_of_sessions}
    :rtype: dict
    :raises HTTPError: if status code is not 20 or 201
    """
    response = get_admin_user().get(User.BASE_SESSION_URL, headers=SECURITY_REQUEST_HEADERS)
    if response.status_code not in [200, 201]:
        raise HTTPError('Unable to retrieve active sessions. Reason "%s"' % response.text, response=response)

    return response.json()


def get_or_create_admin_user(enm_admin_creds_file=None, open_session=True, default_admin=False):
    """
    Creates the administrator user. Gets the administrator user if it already exists.
    Optionally opens an enm session with that user and persists the user for later use.
    Reads credentials file or prompts user on the terminal.

    :param enm_admin_creds_file: File with User credentials.
    :type enm_admin_creds_file: File
    :param open_session: Whether to open a session with the user instance.
    :type open_session: bool
    :param default_admin: Boolean of whether to retrieve the default administrator user
    :type default_admin: bool

    :return: `User` instance
    :rtype: enm_user_2.User
    """
    if enm_admin_creds_file is None:
        enm_admin_creds_file = "/tmp/enmutils/enm-credentials"
    try:
        admin_user = get_admin_user(check_session=True, default_admin=default_admin)
    except:
        admin_user = fetch_credentials_create_user_instance(enm_admin_creds_file, open_session)
    return admin_user


def fetch_credentials_create_user_instance(enm_admin_creds_file, open_session):
    """
    Fetch the user credentials, create and open the user session if required.

    :param enm_admin_creds_file: File with User credentials.
    :type enm_admin_creds_file: File
    :param open_session: Whether to open a session with the user instance.
    :type open_session: bool

    :raises RuntimeError: if there are no credentials or credentials length is not equal to 2

    :return: User instance
    :rtype: `User`
    """
    keep_password = True
    if filesystem.does_file_exist(enm_admin_creds_file):
        credentials = tuple(filesystem.get_lines_from_file(enm_admin_creds_file))
    else:
        credentials, keep_password = load_credentials_from_props_or_prompt_for_credentials()
    if not credentials or len(credentials) != 2:
        raise RuntimeError("Unable to obtain ENM SECURITY_ADMIN credentials")
    return create_the_user_instance_and_log_in_if_specified(credentials, keep_password=keep_password,
                                                            open_session=open_session)


def create_the_user_instance_and_log_in_if_specified(credentials, keep_password=True, open_session=True,
                                                     credentials_prompt=0):
    """
    Create an administrator instance and optionally open a session with that user.

    :param credentials: User credentials in which to create the user instance with.
    :type credentials:  tuple
    :param keep_password: Whether to store the users password.
    :type keep_password: bool
    :param open_session: Whether to open a session with the user instance.
    :type open_session: bool
    :param credentials_prompt: recursive retry to prompt the user for credentials after a failed login.
    :type credentials_prompt: int

    :returns:   enm user
    :rtype:     `enm_user_2.User` instance
    :raises Exception: if there there is an issue with opening the session.
    :raises e: if there is an exception
    """
    log.logger.debug("Creating the {0} User instance.".format(credentials[0]))
    admin_user = User(credentials[0], credentials[1], keep_password=keep_password, is_default_admin=True)
    if not open_session and persistence.get(ADMINISTRATOR_SESSION_KEY) is not None:
        return admin_user
    try:
        admin_user.open_session()
    except Exception as e:
        if "invalid" in str(e) or "valid ENM" in str(e):
            log.logger.debug('Failed to login. Error was {0}'.format(str(e)))
            if credentials_prompt < 1:
                credentials_prompt += 1
                log.logger.debug('Prompting the user for credentials')
                credentials, keep_password = load_credentials_from_props_or_prompt_for_credentials(reprompt=True)
                log.logger.debug('Creating the user instance and trying to log in')
                admin_user = create_the_user_instance_and_log_in_if_specified(credentials, keep_password=keep_password,
                                                                              credentials_prompt=credentials_prompt)
            else:
                log.logger.info("Login failed. Please check username/password and retry."
                                "Please note after 3 failed login attempts the user account will be locked for a "
                                "default of 5 minutes and will be un-able to login")

        else:
            raise e

    return admin_user


def load_credentials_from_props_or_prompt_for_credentials(initial_prompt=INITIAL_PROMPT, username_prompt=USERNAME_PROMPT, password_prompt=PASSWORD_PROMPT, reprompt=False):
    """
    Checks for the presence of a credentials properties file. If it exists, the user credentials are loaded
    from it.
    If there are no credentials in the file, then the end user is prompted for a valid administrator username
    and password.

    :type initial_prompt: str
    :param initial_prompt: The first prompt the end user will receive to ask for valid administrator credentials.
    :type username_prompt: str
    :param username_prompt: The prompt the end user will receive to ask for valid administrator username.
    :type password_prompt: str
    :param password_prompt: The prompt the end user will receive to ask for valid administrator password.
    :type reprompt: bool
    :param reprompt: Boolean value of whether the user will be re prompted to enter credentials.


    :rtype: tuple
    :return: username, password and bool variable of whether to store the password.
    """

    keep_password = True
    credentials = ()
    if not reprompt:
        credentials = config.load_credentials_from_props()
    if reprompt or not credentials:
        keep_password = False
        log.logger.debug("No credentials were found or credentials were invalid. "
                         "Continuing to prompt the user for credentials.")
        credentials = _prompt_for_credentials(initial_prompt, username_prompt, password_prompt)

    return credentials, keep_password


def get_user_key(user_key=None, default_admin=False):
    """
    Retrieves the user key.

    :type user_key
    :param user_key:
    :type default_admin: bool
    :param default_admin: Boolean of whether to return the default administrator user.

    :return: user key
    :rtype: str
    """
    user_key = user_key or WORKLOAD_ADMIN_SESSION_KEY if \
        cache.check_if_on_workload_vm() and persistence.has_key(WORKLOAD_ADMIN_SESSION_KEY) \
        and not default_admin else ADMINISTRATOR_SESSION_KEY

    return user_key


def get_admin_user(check_session=False, default_admin=False, retry=0):
    """
    Gets the admin user instance from persistence.
    If the internal package is installed then, it will retrieve the workload_admin User.
    Otherwise it will retrieve the default admin User

    :type check_session: bool
    :param check_session: Boolean indicator to check if the User session is established
    :type default_admin: bool
    :param default_admin: Boolean indicator that will flag whether to get the default administrator from persistence.
    :param retry: Integer counter for number of attempts to be performed to create admin user
    :type retry: int

    :rtype: enm_user_2.User
    :return: `User` instance
    :raises RuntimeError: if admin does not exist
    """
    log.logger.debug("Getting the workload admin session")
    admin_key = get_user_key(default_admin=default_admin)
    if not is_session_available(user_key=admin_key, check_session=check_session):
        if not retry:
            try:
                fetch_credentials_create_user_instance("/tmp/enmutils/enm-credentials", True)
            except Exception as e:
                log.logger.debug(str(e))
            finally:
                get_admin_user(check_session, default_admin, retry=1)
        else:
            raise RuntimeError('Administrator session not established')
    return persistence.get(admin_key)


def _prompt_for_credentials(initial_prompt, username_prompt, password_prompt):
    """
    B{Prompts the operator for the username and password of an ENM user account with the SECURITY_ADMIN role}

    :param initial_prompt: asking to enter the credential for  enm
    :type initial_prompt: str
    :param username_prompt: asking to enter username
    :type username_prompt: str
    :param password_prompt: asking to enter the password
    :type password_prompt: str
    :rtype: tuple
    :return: 2-element tuple consisting of (username, password)
    """

    log.logger.info(initial_prompt)
    time.sleep(0.1)
    username = raw_input(username_prompt)
    password = getpass.getpass(password_prompt)
    return username, password


def is_session_available(user_key=None, check_session=False):
    """

    :type user_key: str
    :param user_key: String representation of the user key in persistence
    :type check_session: bool
    :param check_session: Boolean indicator, to determine whether or not to check if the session is still available

    :rtype: bool
    :return: boolean if the session is still available
    """
    user_key = get_user_key(user_key)
    if persistence.has_key(user_key):
        user = persistence.get(user_key)
        if check_session:
            return user.is_session_established()
        else:
            return True


def _get_failed_response(method, url, e):
    """
    Returns default failed response object for exceptions that raise errors

    :type method: str
    :param method: type of request made (either post, put, delete or ger)
    :type url: str
    :param url: rest endpoint request was issued to
    :type e: str
    :param e: Exception to get from failed response

    :return: 'Response' Instance
    :rtype:
    """

    response = Response()
    response.status_code = 599
    response.url = url
    response._content = "ENMUtils response - ERROR: {0}\n{1} request to {2} raised this exception.".format(
        str(e), method, url
    )
    response.request = Request()
    response.request.method = method
    response.request.url = url
    return response


def verify_credentials(username, password, enm_url=None):
    """
    B{Determines whether ENM account credentials are valid or not}

    :type username: str
    :param username: ENM username
    :type password: str
    :param password: Password for specified username
    :type enm_url: str
    :param enm_url: URL of the ENM HTTP server that the credentials are to be verified against
    :rtype: boolean
    :return: True if there is iPlanetDirectoryPro in cookies otherwise False
    """
    result = False

    # Format the request payload and then POST it
    payload = {"IDToken1": username, "IDToken2": password}
    enm_url = enm_url or cache.get_apache_url()
    r = requests.post(urljoin(enm_url, SSO_URL), params=payload, verify=False, allow_redirects=False)

    if r.cookies is not None and AUTH_COOKIE_KEY in str(r.cookies):
        result = True

    return result


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


def raise_for_status(response, message_prefix=""):
    """
    Validates the HTTPStatus of the response

    :param response: The HTTPResponse object to query for a userMessage
    :type response: HTTPResponse object
    :param message_prefix: Message to prefix the HTTPError with if raised
    :type message_prefix: str

    :raises HTTPError: raised the status of the response is between 400 and 600
    """
    if 400 <= response.status_code < 600:
        message = build_user_message(response)
        raise HTTPError(message_prefix + message, response=response)


def verify_json_response(response):
    """
    Validates the JSON format of the response

    :param response: The HTTPResponse object to query for a userMessage
    :type response: HTTPResponse object

    :raises EnmApplicationError: if response was not written in JSON format
    """

    try:
        response.json()
    except ValueError:
        raise EnmApplicationError("Unexpected response received {0}".format(response.text))


def check_haproxy_online():
    """
    Check if the haproxy is online or not.
    :return: True if the ENM HAproxy service is online, or does not exist (e.g. in cENM), else False
    :rtype: bool
    """

    log.logger.debug("Checking HAProxy status")
    haproxy_status_cmd = ("/opt/ericsson/enminst/bin/vcs.bsh --groups -g Grp_CS_svc_cluster_haproxy_ext | "
                          "egrep -i online")
    haproxy_status_cloud_cmd = ("sudo consul members | egrep $(sudo consul catalog nodes -service=haproxy| "
                                "egrep -v Node | awk '{print $1}')")
    haproxy_status = False
    with mutexer.mutex('haproxy-online-check', timeout=HAPROXY_DOWNTIME_SECS, persisted=True, log_output=True):
        get_persisted_ha_proxy_value = persistence.get(HAPROXY_OFFLINE_KEY)
        if get_persisted_ha_proxy_value is not None:
            return get_persisted_ha_proxy_value
        if cache.is_emp():
            log.logger.debug("ENM on Cloud detected - running command on EMP")
            command_response = shell.run_cmd_on_vm(haproxy_status_cloud_cmd, cache.get_emp())
            if not command_response.rc and "alive" in command_response.stdout:
                haproxy_status = True
        elif cache.is_enm_on_cloud_native():
            log.logger.debug("ENM on Cloud native detected - HAproxy does not exist")
            return True
        else:
            log.logger.debug("ENM on Physical detected - running command on LMS")
            command_response = shell.run_cmd_on_ms(shell.Command(haproxy_status_cmd))
            if not command_response.rc and "ONLINE" in command_response.stdout:
                haproxy_status = True

        log.logger.debug("Status of Haproxy : {0}".format(haproxy_status))
        if not haproxy_status:
            persistence.set(HAPROXY_OFFLINE_KEY, haproxy_status, HAPROXY_DOWNTIME_SECS)
        return haproxy_status


class RolesUpdateError(Exception):
    pass


@persistable
class EnmRole(object):

    BASE_URL = "/oss/idm/rolemanagement/roles"
    FULL_URL = "{0}/".format(BASE_URL)
    USECASES_URL = "/oss/idm/rolemanagement/usecases"

    def __init__(self, name, description="", enabled=True, user=None, targets=None):
        """
        Constructor for ENM System Role object

        :type name: str
        :param name: enm name
        :type description: str
        :param description: enm role description
        :type enabled: bool
        :param enabled: is enm role enabled
        :type user: enm_user_2.User
        :param user: User instance
        :type targets: enm_user_2.Target
        :param targets: enm role targets
        """

        self.name = name
        self.description = description
        self.targets = targets if targets is not None else {Target("ALL")}
        self.enabled = enabled
        self.user = user or get_admin_user()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)

    def _teardown(self):
        """
        Secret teardown method
        """

        self._delete()

    def _create(self, additional_json=None):
        create_as = self.user or get_admin_user()

        existing_targets = Target.get_existing_targets(user=self.user)
        for target in self.targets:
            if target not in existing_targets:
                target.create(self.user)

        body = {
            "name": self.name,
            "description": self.description,
            "status": "ENABLED",
        }

        if additional_json:
            body.update(additional_json)

        response = create_as.post(self.BASE_URL, json=body, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not create role: ")

    def _delete(self):
        """
        Deletes a Role on ENM
        """

        response = self.user.delete_request(self.FULL_URL + self.name, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not delete role: ")
        log.logger.debug("Successfully deleted ENM Role {0}".format(self.name))

    def _update(self, additional_json):
        body = {
            "type": "custom",
            "name": self.name,
            "description": self.description,
            "status": "ENABLED" if self.enabled else "DISABLED"
        }

        if additional_json:
            body.update(additional_json)

        response = self.user.put(self.FULL_URL + self.name, json=body, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not update role: ")
        log.logger.debug("Successfully updated ENM Role {0}".format(self.name))

    @classmethod
    def get_role_by_name(cls, name, user=None):
        """
        Get the required ENM Role
        :param name: name of role which needs to be fetched
        :type name: str
        :param user: user used to fetch the role
        :type user: enm_user_2.User
        :return: role if it exists
        :rtype: EnmRole
        """
        log.logger.debug("Getting role {0} if it exists on ENM".format(name))
        role_info = cls.get_role_info_from_enm(name=name, user=user, message_prefix="Could not get ENM role: ")

        if role_info["type"] in ["system", "application"]:
            return EnmRole(role_info["name"], description=role_info["description"], enabled=role_info["status"] == "ENABLED", user=user)
        elif role_info["type"] == "com":
            return EnmComRole(role_info["name"], description=role_info["description"], enabled=role_info["status"] == "ENABLED", user=user)
        else:
            sub_roles = set(EnmComRole(sub_role["name"], description=sub_role["description"], enabled=sub_role["status"] == "ENABLED", user=user) for sub_role in role_info["roles"])
            if role_info["type"] == "comalias":
                return EnmRoleAlias(role_info["name"], sub_roles, description=role_info["description"], enabled=role_info["status"] == "ENABLED", user=user)
            else:
                capabilities = set(RoleCapability(resource, action, user=user) for resource, actions in role_info["policy"].iteritems() for action in actions)
                return CustomRole(role_info["name"], sub_roles, capabilities, description=role_info["description"], enabled=role_info["status"] == "ENABLED", user=user)

    @classmethod
    def get_all_roles(cls, user=None):
        """
        Get all role objects from ENM
        :param user: `User` instance
        :type user: enm_user_2.User
        :rtype: list
        :return: list of dicts, containing enm roles
        """
        log.logger.debug("Getting all role objects from ENM")
        user = user or get_admin_user()
        response_json = cls.get_role_info_from_enm(user=user)
        roles = set()
        for role_info in response_json:
            if role_info["type"] == "system" or role_info["type"] == "cpp":
                role = EnmRole(role_info["name"], description=role_info["description"],
                               enabled=role_info["status"] == "ENABLED", user=user)
            elif role_info["type"] == "com":
                role = EnmComRole(role_info["name"], description=role_info["description"],
                                  enabled=role_info["status"] == "ENABLED", user=user)
            else:
                role = cls.get_role_by_name(role_info["name"], user=user)

            roles.add(role)
        return roles

    @classmethod
    def check_if_role_exists(cls, role_name, user=None):
        """
        Check if the role already exists on ENM
        :param role_name: name of the role which needs to be checked
        :type role_name: str
        :param user: enm user which is used to make the request
        :type user: User instance
        :return: None if role already exists or dict of all existing roles if it does not already exist
        :rtype: dict
        """
        log.logger.debug("Checking if role already exists on ENM")
        response_json = cls.get_role_info_from_enm(user=user)
        return None if any(role_info["name"] == role_name for role_info in response_json) else response_json

    @classmethod
    def get_all_role_names(cls, user=None, role_details=None):
        """
        Get the names of all existing roles on ENM
        :param user: enm user which is used to make the request
        :type user: User instance
        :param role_details: dictionary with all the existing roles information
        :type role_details: dict
        :return: list of names of existing roles on ENM
        :rtype: list
        """
        log.logger.debug("Getting names of all existing roles on ENM")
        response_json = role_details or cls.get_role_info_from_enm(user=user)
        return [role_info["name"] for role_info in response_json]

    @classmethod
    def get_role_info_from_enm(cls, user=None, name="", message_prefix=None):
        """
        Get existing roles from ENM
        :param user: enm user which is used to make the request
        :type user: User instance
        :param name: name of the role to be fetched
        :type name: str
        :param message_prefix: prefix used before logging the actual failure reason
        :type message_prefix: str
        :return: return information about all exisitng roles
        :rtype: dict
        """
        log.logger.debug("Getting existing roles from ENM endpoint")
        message_prefix = message_prefix or "Could not get ENM roles: "
        user = user or get_admin_user()
        response = user.get("{0}{1}".format(cls.FULL_URL, name), headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix=message_prefix)
        return response.json()


@persistable
class EnmComRole(EnmRole):
    def __init__(self, name, targets=None, description="", enabled=True, user=None):
        """

        :param name: EnmComRole name
        :type name: str
        :param targets: EnmComRole targets
        :type targets: set[Target]
        :param description: EnmComRole description
        :type description: str
        :param enabled: is EnmComRole enaled
        :type enabled: bool
        :param user: User instance
        :type user: enm_user_2.User
        """

        super(EnmComRole, self).__init__(name, description, enabled, user)
        self.targets = targets if targets else {Target("ALL")}

    def create(self):
        self._create(additional_json={"type": "com"})

    def delete(self):
        self._delete()

    def update(self):
        self._update(additional_json={"type": "com"})


@persistable
class EnmRoleAlias(EnmRole):
    def __init__(self, name, roles, targets=None, description="", enabled=True, user=None):
        """
        :type name: string
        :type roles: set[EnmComRole]
        :type targets: set[Target]
        :type description: string
        :type enabled: bool
        :type user: enm_user_2.User
        """
        super(EnmRoleAlias, self).__init__(name, description, enabled, user)
        self.roles = roles
        self.targets = targets or {Target("ALL")}

    def create(self):
        existing_roles = self.get_all_role_names()
        for role in self.roles:
            if role.name not in existing_roles:
                role.create()

        additional_json = {
            "type": "comalias",
            "assignRoles": [role.name for role in self.roles]
        }
        self._create(additional_json=additional_json)

    def delete(self):
        self._delete()


@persistable
class CustomRole(EnmRole):
    def __init__(self, name, roles=frozenset(), capabilities=frozenset(), description="", enabled=True, user=None,
                 policies=None, targets=None):
        """
        :type name: string
        :type roles: set[EnmComRole]
        :type capabilities: set[RoleCapability]
        :type description: string
        :type enabled: bool
        :type user : enm_user_2.User
        type policies: dict
        type targets: list[Target]
        """
        super(CustomRole, self).__init__(name, description, enabled, user, targets)
        self.capabilities = capabilities
        self.roles = roles
        self.policies = policies if policies is not None else {}

    def create(self, role_details=None):
        """
        Creates a custom role and sub roles
        :param role_details: dictionary information for all existing roles
        :type role_details: dict
        """
        log.logger.debug("Attempting to create custom role: {0}".format(self.name))
        existing_roles = self.get_all_role_names(user=self.user, role_details=role_details)
        for role in self.roles:
            if role.name not in existing_roles:
                role.create()

        capabilities_json = defaultdict(list)
        for capability in self.capabilities:
            capabilities_json[capability.resource].append(capability.operation)

        additional_json = {
            "type": "custom",
            "assignRoles": [role.name for role in self.roles],
            "policy": dict(capabilities_json),
        }
        self._create(additional_json=additional_json)

    def delete(self):
        self._delete()

    def update(self):
        """
        Updates a Custom ENM User Role
        """

        existing_roles = self.get_all_role_names(user=self.user)
        for role in self.roles:
            if role.name not in existing_roles:
                role.create()

        capabilities_json = defaultdict(list)
        for capability in self.capabilities:
            capabilities_json[capability.resource].append(capability.operation)

        additional_json = {
            "type": "custom",
            "assignRoles": [role.name for role in self.roles],
            "policy": dict(capabilities_json)
        }
        self._update(additional_json=additional_json)


@persistable
class RoleCapability(object):
    USECASES_URL = "/oss/idm/rolemanagement/usecases"

    def __init__(self, resource, operation, description="", user=None):
        self.resource = resource
        self.operation = operation
        self.description = description
        self.user = user or get_admin_user()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.resource == other.resource and self.operation == other.operation

    def __str__(self):
        return "{}:{}".format(self.resource, self.operation)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)

    @classmethod
    def get_all_role_capabilities(cls, user=None):
        """

        :param user: User instance
        :type user: enm_user_2.user
        :return: set list of all role capabilities
        :rtype: set[RoleCapability]
        """
        user = user or get_admin_user()
        response = user.get(cls.USECASES_URL, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not get role capabilities: ")
        return set(RoleCapability(capability["resource"], capability["action"], capability["description"], user) for capability in response.json())

    @classmethod
    def get_role_capabilities_for_resource(cls, resource, user=None):
        """
        :param resource: string
        :type resource:
        :param user: User instance
        :type user: enm_user_2.User
        :return: set list of role capabilities in resource
        :rtype: set[RoleCapability]
        """
        return set(role_capability for role_capability in cls.get_all_role_capabilities(user) if role_capability.resource == resource)

    @classmethod
    def get_role_capabilities_for_resource_based_on_operation(cls, resource, operation, user=None):
        """
        Get role capabilities for resource based on operation.
        :param resource: capability resource name
        :type resource: str
        :param operation: type of resource operation
        :type operation: str
        :param user: User instance
        :type user: enm_user_2.User
        :return: set list of role capabilities in resource
        :rtype: set[RoleCapability]
        """
        return set(role_capability for role_capability in cls.get_all_role_capabilities(user)
                   if role_capability.resource == resource and role_capability.operation == operation)


@persistable
class Target(object):

    BASE_URL = "/oss/idm/targetgroupmanagement/targetgroups"
    UPDATE_URL = BASE_URL + "/{target}/description"
    GET_ASSIGNMENT_URL = BASE_URL.replace('targetgroups', '') + "targets?targetgroups={target}"
    UPDATE_ASSIGNMENT_URL = BASE_URL.replace('targetgroups', 'modifyassignment')
    DELETE_URL = BASE_URL + "/{target}"

    def __init__(self, name, description=""):
        """

        :param name: Target name
        :type name: string
        :param description: Target description
        :type description: string
        """

        self.name = name
        self.description = description

    @property
    def exists(self):
        for existing_target in self.get_existing_targets():
            if self.name == existing_target.name:
                return True

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)

    @classmethod
    def get_existing_targets(cls, user=None):
        user = user or get_admin_user()

        response = user.get(cls.BASE_URL, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not get ENM target groups: ")

        existing_targets = set()
        for target_info in response.json():
            existing_targets.add(Target(target_info["name"], target_info["description"]))

        return existing_targets

    def get_assigned_nodes(self):
        """
        Queries ENM to see if the target groups currently has node assignment

        :rtype: set
        :return: Set containing the nodes assigned to the target group
        """
        existing_nodes = set()

        response = self.user.get(self.GET_ASSIGNMENT_URL.format(target=self.name), headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not get ENM target group's assigned nodes: ")

        for node_dict in response.json():
            existing_nodes.add(node_dict.get("name"))

        return existing_nodes

    def create(self, create_as=None):
        """
        :raises HTTPRequestException: If an invalid response was returned
        """
        create_as = create_as or get_admin_user()

        body = {
            "name": self.name,
            "description": self.description
        }
        response = create_as.post(self.BASE_URL, json=body, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not create target group: ")

    def update(self, description, user=None):
        """
        Update the Target Group description

        :type description: str
        :param description: Updated description of the Target Group
        :type user: `enm_user_2.User`
        :param user: ENM user who will perform the update
        """

        user = user or get_admin_user()
        body = {
            "description": description,
        }

        response = user.put(self.UPDATE_URL.format(target=self.name), json=body, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not update target group: ")
        log.logger.debug("Successfully updated ENM Target Group {0}".format(self.name))

    def update_assignment(self, nodes, user=None):
        """
        Update the Target Group assignment

        :type nodes: `enm_node.Node`
        :param nodes: ENM nodes to assign to the Target Group
        :type user: enm_user_2.User
        :param user: User instance
        :raises EnvironError: if there is no nodes
        """

        user = user or get_admin_user()
        if not nodes:
            raise EnvironError("Cannot update assignment without nodes.")
        body = []
        for node in set(nodes):
            body.append({"action": "ADD", "targetGroup": self.name, "target": node.node_id})
        response = user.put(self.UPDATE_ASSIGNMENT_URL, json=body, headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not update target group: ")
        log.logger.debug("Successfully updated ENM Target Group {0}".format(self.name))

    def delete(self, user=None):
        """
        Deletes a Target Group on ENM

        :type user: `enm_user_2.User`
        :param user: ENM user who will perform the deletion
        """

        user = user or get_admin_user()
        response = user.delete_request(self.DELETE_URL.format(target=self.name), headers=SECURITY_REQUEST_HEADERS)
        raise_for_status(response, message_prefix="Could not delete target: ")
        log.logger.debug("Successfully deleted ENM target group {0}".format(self.name))

    def _teardown(self):
        """
        Secret teardown method
        """

        self.delete()
