from retrying import retry

from enmutils.lib import cache
from enmutils.lib import log, mutexer
from enmutils.lib.enm_user_2 import User, SessionTimeoutException, get_user_privileges, get_all_sessions, EnmRole
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_apache_url

BASE_USER_URL = "/oss/idm/usermanagement/users"
USER_COUNT_MUTEX_KEY = "user-count-key"
SERVICE_NAME = "usermanager"
USER_COUNT_THRESHOLD = 5000


def check_user_count_threshold():
    """
    Checks if user count threshold of 5000 is reached
    """
    log.logger.debug("Checking if user count threshold of 5000 is reached")
    try:
        if (get_total_enm_user_count(
                get_workload_admin_user(), "{0}/{1}".format(log.SERVICES_LOG_DIR, SERVICE_NAME)) >=
                USER_COUNT_THRESHOLD):
            message = "Unable to complete user creation request, ENM maximum: {0} user(s) capability reached.".format(
                USER_COUNT_THRESHOLD)
            rc = 409
            return message, rc
    except Exception as e:
        return "Could not create user(s) on ENM due to :: {0}.".format(str(e.message)), 500


def get_total_enm_user_count(user, log_path):
    """
    Query ENM for the local and federated user information

    :param user: User who will perform the GET requests
    :type user: `enm_user_2.User`
    :param log_path: Log path of the caller
    :type log_path: str

    :raises exception: (EnmApplicationError) raised if no user count or GET request fails.

    :return: Total length of the json response(s)
    :rtype: int
    """
    with mutexer.mutex(USER_COUNT_MUTEX_KEY, log_output=True):
        error_msg = "Unable to retrieve ENM user count, please check logs: [{0}] for debug information".format(log_path)
        exception = EnmApplicationError(error_msg)
        users = []
        try:
            response = user.get(BASE_USER_URL)
            users.extend([_.get('username') for _ in response.json()])
        except Exception as e:
            log.logger.debug(str(e))
            raise exception
        if not users:
            raise exception
        return len(set(users))


def fetch_and_set_enm_url_from_deploymentinfomanager():
    """
    Function to check if ENM URL for usermanager is up to date
    """
    log.logger.debug("Checking and updating ENM URL from deploymentinfomanager service")
    hostname_cache = cache.get('httpd-hostname')
    hostname_deployment = get_apache_url()

    if hostname_deployment:
        hostname_deployment = hostname_deployment.replace("https://", "")
        if hostname_deployment != hostname_cache:
            log.logger.debug("Updating ENM URL for usermanager: '{0}' to '{1}'".format(hostname_cache,
                                                                                       hostname_deployment))
            cache.set("httpd-hostname", "{0}".format(hostname_deployment))
        else:
            log.logger.debug("Usermanager and deploymentinfomanager services have same ENM URL")
    else:
        log.logger.debug("Unable to fetch ENM URL from deploymentinfomanager service")


@retry(retry_on_exception=lambda e: isinstance(e, SessionTimeoutException), wait_fixed=5000,
       stop_max_attempt_number=2)
def get_enm_users_list():
    """
    Get the list of existing users on ENM

    :raises SessionTimeoutException: raised is the user is unable to establish a session

    :return: List of the existing users by username in ENM
    :rtype: list
    """
    log.logger.debug("Retrieving list of users currently defined on ENM")
    users_list = User.get_usernames(user=get_workload_admin_user())
    log.logger.debug("Total Number of users on ENM: {0}".format(len(users_list)))
    return users_list


def get_enm_users_with_matching_user_roles(profile_name, user_roles):
    """
    Get list of users on ENM that have certain roles

    :param profile_name: Name of Profile
    :type profile_name: str
    :param user_roles: List of User roles
    :type user_roles: list
    :return: List of usernames
    :rtype: list
    """
    log.logger.debug("Checking users in ENM to determine which ones have matching list of user roles")
    profile_usernames = [username for username in get_enm_users_list() if profile_name in username]

    enm_users_with_matching_user_roles = []
    for username in profile_usernames:
        log.logger.debug("Fetching ENM roles for user {0}".format(username))
        enm_role_names = set([str(enm_role.name) for enm_role in get_user_privileges(username)])
        if enm_role_names == set([str(role) for role in user_roles]):
            enm_users_with_matching_user_roles.append(username)

    log.logger.debug("Found {0} matching user(s)".format(len(enm_users_with_matching_user_roles)))
    return enm_users_with_matching_user_roles


def delete_users_from_enm_by_usernames(username_list):
    """
    Delete specific users from ENM

    :param username_list: List of usernames to use to locate the user object
    :type username_list: list
    """
    log.logger.debug("Deleting users on ENM by username: {0}".format(username_list))
    admin_user = get_workload_admin_user()
    for username in username_list:
        log.logger.debug("Attempting to delete user {0} from ENM.".format(username))
        user = User(username=username)
        user.delete(delete_as=admin_user)
        log.logger.debug("User {0} deleted from ENM.".format(username))
    log.logger.debug("Deletion of users complete")


def get_sessions_info(profiles):
    """
    Generates number of sessions per profile and top 10 sessions hoarders

    :param profiles: list of profile names
    :type profiles: list

    :return: Dictionary of numbers of sessions per profile and list of top 10 sessions hoarders
    :rtype: tuple
    """
    log.logger.debug("Generating top 10 sessions hoarders list and sessions per profile dictionary")
    profile_sessions = {profile: 0 for profile in profiles}
    session_hoarders = None
    try:
        response = get_all_sessions()
    except Exception as e:
        log.logger.debug("Exception thrown while getting sessions. Exception: {0}".format(str(e)))
        total_sessions = profile_sessions["total"] = "UNKNOWN"
        total_logged_in = profile_sessions["logged_in"] = "UNKNOWN"
    else:
        for user_name, session in response["users"].iteritems():
            for profile_name in profile_sessions.keys():
                if profile_name.lower() in user_name:
                    profile_sessions[profile_name] += session

        total_sessions = profile_sessions["total"] = sum(response["users"].values())
        total_logged_in = profile_sessions["logged_in"] = len(response["users"].values())
        session_hoarders = sorted(response['users'].items(), key=lambda x: x[1], reverse=True)[:10]
    log.logger.debug("Total sessions found: {0}. Total logged in users: {1}".format(total_sessions, total_logged_in))

    return profile_sessions, session_hoarders


def delete_existing_users(profile_name, roles):
    """
    Checks existing users for profile and deletes them if any
    :param profile_name: name of the profile
    :type profile_name: str
    :param roles: roles of the profile
    :type roles: list
    """
    log.logger.debug("Checking for existing users for {0}".format(profile_name))
    users = get_enm_users_with_matching_user_roles(profile_name, roles)
    if users:
        log.logger.debug("Attempting to delete {0} user(s) for [{1}] profile".format(users, profile_name))
        delete_users_from_enm_by_usernames(users)


def generate_user_info_list(users):
    """
    Generates list of users info dicts to be used to create BasicUser
    :param users: list of users dicts
    :type users: list
    :return: list of users with info needed to create BasicUser
    :rtype: list
    """
    return [{"username": user.username, "password": user.password, "keep_password": user.keep_password,
             "persist": user.persist, "_session_key": user._session_key} for user in users]


def create_user_role_objects(roles):
    """
    Creates user role objects from names of roles
    :param roles: list of role names
    :type roles: list
    :return: list of role objects
    :rtype: list
    """
    log.logger.debug("Creating role: {}".format(roles))
    admin_user = get_workload_admin_user()
    return list(set(EnmRole(role, user=admin_user) for role in roles))
