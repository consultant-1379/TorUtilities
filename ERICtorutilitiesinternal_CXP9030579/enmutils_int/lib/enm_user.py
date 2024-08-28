# ********************************************************************
# Name    : ENM User
# Summary : Mainly responsible for creating WORKLOAD ADMIN user.
#           Allows creation, deletion and retrieval of the workload
#           admin user or the default admin user, also provides the
#           child class for creating a Custom User object in ENM.
# ********************************************************************

import base64
from os import getpid
from socket import gethostname

from requests.exceptions import HTTPError
from retrying import retry

from enmutils.lib import enm_user_2, log, persistence, cache, mutexer
from enmutils.lib.enm_user_2 import User, WORKLOAD_ADMIN_SESSION_KEY
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.filesystem import write_data_to_file
from enmutils.lib.headers import SECURITY_REQUEST_HEADERS
from enmutils.lib.timestamp import get_human_readable_timestamp
from enmutils_int.lib.helper_methods import get_local_ip_and_hostname

WORKLOAD_ADMIN_PASSWORD = '?Assw0rd'
WORKLOAD_ADMIN_USER_MUTEX = "workload-admin-creation"
WORKLOAD_ADMIN_USERNAME = None


def workload_admin_with_hostname():
    """
    Function to return workload admin with hostname to make the admin username unique

    @return: name of the workload admin with hostname
    @rtype: str
    """
    global WORKLOAD_ADMIN_USERNAME
    WORKLOAD_ADMIN_USERNAME = WORKLOAD_ADMIN_USERNAME or 'workload_admin_{0}'.format(gethostname())
    return WORKLOAD_ADMIN_USERNAME


def get_or_create_admin_user(enm_admin_creds_file=None, default_admin=False):
    """
    Creates the admin user, opens enm session and persists the user for later use;
    Reads credentials file or prompts user on the terminal in production environs.
    Should only be called from the tool level.

    :return: administrator user object
    :rtype: `enm_user_2.User`
    """
    return enm_user_2.get_or_create_admin_user(enm_admin_creds_file=enm_admin_creds_file, default_admin=default_admin)


def get_admin_user():
    """
    Gets the admin user instance from persistence

    :raises RuntimeError: if admin does not exist
    :rtype: User
    :return: `User` instance
    """
    return enm_user_2.get_admin_user(default_admin=True)


def user_exists(search_as, search_for_username=WORKLOAD_ADMIN_USERNAME):
    """
    Check if the supplied user exists

    :param search_as: User who will perform the query
    :type search_as: `enm_user_2.User` instance
    :param search_for_username:
    :type search_for_username: str

    :return: Boolean indicating if the user was found or not
    :rtype: bool
    """
    search_for_username = search_for_username or workload_admin_with_hostname()
    log.logger.debug("Checking if user {0} exists.".format(search_for_username))
    response = search_as.get(search_as.USER_URL.format(username=search_for_username))
    if response.ok:
        log.logger.debug("User {0} found.".format(search_for_username))
        return True
    log.logger.debug("User {0} not found.".format(search_for_username))


def get_workload_admin_user():
    """
    Retrieve and cache the workload admin user from persistence if available and re-establish the user session.
    If the user is not on the workload vm, the default administrator user will be retrieved and cached.

    :returns:   Workload admin user
    :rtype:     `enm_user_2.User` instance
    """
    log.logger.debug("Retrieving the workload admin or the administrator user.")
    enm_workload_admin_user_key = "cached_workload_admin_user"
    if not cache.has_key(enm_workload_admin_user_key):
        log.logger.debug("Retrieving the relevant admin user.")
        if cache.check_if_on_workload_vm():
            log.logger.debug("Retrieving the workload admin user and re-establishing session")
            user_key = persistence.get(WORKLOAD_ADMIN_SESSION_KEY)
            if user_key:
                user = verify_workload_admin_user_login(user_key)
            else:
                with mutexer.mutex(WORKLOAD_ADMIN_USER_MUTEX, persisted=True, log_output=True):
                    user = create_workload_admin_user_instance_and_login()
        else:
            log.logger.debug("Retrieving the default admin user")
            user = get_or_create_admin_user(default_admin=True)
        log.logger.debug("{0} key is currently not set. Setting the key for user {1}".format(
            enm_workload_admin_user_key, user.username))
        cache.set(enm_workload_admin_user_key, user)
        log.logger.debug('{0} user is now cached'.format(user.username))

    return cache.get(enm_workload_admin_user_key)


def create_workload_admin_user_instance_and_login():
    """
    Creates a workload admin user instance.
    This instance is used to try to login as the workload admin user as,
    the user was not in persistence on a previous check but it might be in ENM.

    """
    workload_admin_with_hostname()
    log.logger.debug('Creating the workload admin user instance.')
    workload_admin_user = User(username=WORKLOAD_ADMIN_USERNAME,
                               password=create_password_for_workload_admin(),
                               roles=["ADMINISTRATOR", "SECURITY_ADMIN"], keep_password=True,
                               persist=True, email="workload@workload.com",
                               establish_session=True, is_default_admin=True)
    user = verify_workload_admin_user_login(workload_admin_user)
    return user


def verify_workload_admin_user_login(user):
    """
    Retrieve the persisted workload admin user.

    If the user is not in ENM then create a new workload admin user.

    :param user: User who will perform the query
    :type user:  'enm_user_2.User` instance

    :raises e:  Exception raised if there is an issue with re-establishing the session.

    :returns:   Workload admin user
    :rtype:     'enm_user_2.User' instance
    """
    try:
        workload_admin_with_hostname()
        log.logger.debug('Trying to re-establish the session for the user {0}.'.format(WORKLOAD_ADMIN_USERNAME))
        user.is_session_established()
        log.logger.debug("Successfully retrieved the user {0} from persistence and re-established session."
                         .format(WORKLOAD_ADMIN_USERNAME))
        return user
    except Exception as e:
        if "Invalid login, credentials are invalid" in str(e) or "valid ENM" in str(e) or "401" in str(e):
            log.logger.debug(
                'Exception occurred: {0}. Starting creation of user {1}.'.format(e, WORKLOAD_ADMIN_USERNAME))
            admin_user = enm_user_2.get_or_create_admin_user(default_admin=True)
            return create_workload_admin_user(admin_user)
        log.logger.debug("There has been an issue re-establishing the session. Error: {0}".format(e))
        raise e


@retry(retry_on_exception=lambda e: isinstance(e, RuntimeError), wait_exponential_multiplier=5000,
       stop_max_attempt_number=3)
def create_workload_admin_user(create_as):
    """
    Create the workload admin user

    :param create_as: User who will perform the query
    :type create_as: `enm_user_2.User` instance

    :returns:   Workload admin user
    :rtype:     `enm_user_2.User` instance
    """
    workload_admin_with_hostname()
    log.logger.debug("Starting creation of user {0}.".format(WORKLOAD_ADMIN_USERNAME))
    workload_admin_user = User(username=WORKLOAD_ADMIN_USERNAME,
                               password=create_password_for_workload_admin(),
                               first_name="workload profiles", last_name="DO NOT MODIFY",
                               description="DO NOT MODIFY",
                               roles=["ADMINISTRATOR", "SECURITY_ADMIN"],
                               keep_password=True, persist=True,
                               email="workload@workload.com", establish_session=True, is_default_admin=True)
    workload_admin_user.create(create_as=create_as)
    log.logger.debug("Successfully created user {0}.".format(WORKLOAD_ADMIN_USERNAME))
    store_workload_admin_creator_info_in_file()

    return workload_admin_user


def store_workload_admin_creator_info_in_file():
    """
    Function to store information related to workload admin creattion i.e. pid and creation date/time

    @param username: name of the user created
    @type: str
    """
    workload_admin_with_hostname()
    file_path = '/home/enmutils/.workload-admin-creation-info'
    log.logger.debug("Storing workload admin creation info in {0}".format(file_path))
    pid = getpid()
    dateandtime = get_human_readable_timestamp()
    line = '{0}\tUser {1} created by process {2}\n'.format(dateandtime, WORKLOAD_ADMIN_USERNAME, pid)
    file_appended = write_data_to_file(line, file_path, append=True)
    if file_appended:
        log.logger.debug("Successlly stored information about workload admin creation.")
    else:
        log.logger.debug("Failed to store information related to workload admin creation.")


def create_password_for_workload_admin():
    """
    Creates the password for the workload admin user
    and encodes it. If the password it greater then 32 characters long
    it will use a default password.

    :returns:   Workload admin password
    :rtype:     str
    """
    log.logger.debug("Retrieving the hostname of the workload VM")
    _, host = get_local_ip_and_hostname(get_ip=False)
    password = host + "_" + WORKLOAD_ADMIN_PASSWORD

    if len(base64.b64encode(password)) > 32:
        log.logger.debug("Retrieving default password")
        password = WORKLOAD_ADMIN_PASSWORD

    return base64.b64encode(password)


def recreate_deleted_user(username, user_roles, user=None):
    """
    Recreate the deleted ENM user

    :type username: str
    :param username: user name of deleted user
    :type user_roles: list
    :param user_roles: List of `enm_user_2.EnmRole` instances to be apply
    :type user: enm_user_2.User
    :param user: User instance

    :raises EnmApplicationError: when user creation failed.
    """
    try:
        user_info = get_user_info(username, user)
    except Exception:
        user_info = None
    if not user_info:
        log.logger.debug("Recreating the deleted user: {0}".format(username))
        user = User(username, "TestPassw0rd", roles=user_roles, keep_password=True)
        try:
            user.create()
            log.logger.debug("{0} user recreated successfully".format(username))
        except Exception as e:
            raise EnmApplicationError(e.message)


def get_user_info(username, user=None):
    """
    Gets user information based on username from ENM.

    :type username: str
    :param username: ENM username
    :type user: enm_user_2.User
    :param user: User instance
    :return: The user information
    :rtype: dict
    :raises HTTPError: if user information not found in ENM.
    """
    user = user or get_admin_user()
    response = user.get(User.USER_URL.format(username=username), headers=SECURITY_REQUEST_HEADERS)

    if not response.ok:
        raise HTTPError('Unable to retrieve user information. Reason "%s"' % response.text, response=response)

    log.logger.debug("Successfully fetched user information '{0}'. response = '{1}'".format(username, response.text))

    return response.json()


class CustomUser(User):

    def __init__(self, *args, **kwargs):
        """
        Custom Load user constructor

        :param args: __builtin__ list
        :type args: list
        :param kwargs: __builtin__ dict
        :type kwargs: dict
        """
        super(CustomUser, self).__init__(*args, **kwargs)
        self.roles = kwargs.pop('roles', list())
        self.targets = kwargs.get('targets', list())
        self.auth_mode = kwargs.get('authmode', None)

    def create(self, create_as=None):
        """
        Creates the user in ENM

        :type create_as: enmutils.lib.enm_user_2.User
        :param create_as: user instance to use for creating the new user.
        :type create_as: `enm_user_2.User`

        :raises HTTPError: raised if POST fails
        """
        create_as = create_as or get_or_create_admin_user()
        payload = {
            "username": self.username,
            "password": self.password,
            "status": self.status,
            "name": self.first_name,
            "surname": self.last_name,
            "email": self.email,
            "description": self.description,
            "passwordResetFlag": not self.password_reset_disabled,
            "privileges": [],
            "authMode": self.auth_mode if self.auth_mode else 'local'
        }

        for role in self.roles:
            for target in self.targets:
                payload["privileges"].append({
                    "role": role.name,
                    "targetGroup": target.name
                })

        response = create_as.post(self.BASE_URL, json=payload, headers=SECURITY_REQUEST_HEADERS)
        if response.status_code not in [200, 201]:
            msg = response.json()["userMessage"] if (response.json() and
                                                     "userMessage" in response.json()) else str(response)
            raise HTTPError('User "{0}" with {1} roles failed to create. Reason "{2}"'
                            .format(self.username, len(self.roles), msg), response=response)
        log.logger.debug("Successfully created user {0} with role: {1}"
                         .format(self.username, ','.join(str(role) for role in self.roles)))
