import datetime
import json

from flask import Blueprint, abort, request

from enmutils.lib import enm_user_2, log, persistence
from enmutils_int.lib.common_utils import delete_profile_users, create_users_operation
from enmutils_int.lib.enm_user import get_workload_admin_user, workload_admin_with_hostname
from enmutils_int.lib.services import usermanager_helper_methods as helper
from enmutils_int.lib.services.custom_queue import CustomContainsQueue
from enmutils_int.lib.services.service_common_utils import (get_json_response, abort_with_message,
                                                            create_and_start_once_off_background_scheduled_job,
                                                            create_and_start_background_scheduled_job)
from enmutils_int.lib.services.service_values import URL_PREFIX

SERVICE_NAME = "usermanager"
USER_COUNT_THRESHOLD = 5000
application_blueprint = Blueprint(SERVICE_NAME, __name__, url_prefix=URL_PREFIX)

DELETION_QUEUE = CustomContainsQueue()
SCHEDULER_INTERVAL_MINS = 60


def at_startup():
    """
    Start up function to be executed when service is created
    """
    log.logger.debug("Running startup function")
    create_and_start_background_scheduled_job(helper.fetch_and_set_enm_url_from_deploymentinfomanager,
                                              24 * SCHEDULER_INTERVAL_MINS,
                                              "{0}_DAILY".format(SERVICE_NAME), log.logger)
    log.logger.debug("Startup complete")


def enm_users():
    """
    (Simple) Route to GET ENM username's

    GET /enm/users

    :raises HTTPException: raised if GET request fails, defaults to 404

    :return: List of ENM username's
    :rtype: list
    """
    try:
        return json.dumps(helper.get_enm_users_list())
    except Exception as e:
        log.logger.debug("Could not retrieve list of enm username's, error encountered :: {0}.".format(str(e)))
        status_code = getattr(e.response, 'status_code', 404) if hasattr(e, 'response') else 404
        abort(status_code)


def get_users():
    """
    Route to GET user information from the database

    GET /users
    GET /users?username=<username>
    GET /users?profile=<profile_name>

    :raises HTTPException: 404 raised if GET request fails

    :return: List of DBUser instances or single DBUser instance
    :rtype: List or `DBUser`
    """
    username = request.args.get('username')
    profile_name = request.args.get('profile')
    user_roles = request.args.get('user_roles')
    try:
        return json.dumps(get_users_info(username, profile_name, user_roles))
    except Exception as e:
        log.logger.debug("Could not locate user(s) in database, error encountered :: {0}.".format(str(e)))
        abort(404)


def get_users_info(username, profile_name, user_roles):
    """
    Get users information

    :param username: Name of user
    :type username: str
    :param profile_name: Name of profile
    :type profile_name: str
    :param user_roles: Comma separated list of user roles
    :type user_roles: str
    :return: list
    :rtype: list
    """
    enm_users_list = []
    try:
        enm_users_list = helper.get_enm_users_list()
    except Exception as e:
        log.logger.debug("Failed to retrieve ENM Users list, error encountered: {0}".format(str(e)))
    if username:
        user = persistence.get("{0}_session".format(username))
        users = [user] if user else []
    elif profile_name:
        users = [persistence.get(key) for key in persistence.get_all_default_keys() if
                 key.startswith(profile_name) and key.endswith("session")]
        if user_roles:
            users = get_users_with_matching_user_roles(users, user_roles)
    else:
        users = [persistence.get(key) for key in persistence.get_all_default_keys() if key.endswith("session")]
    if enm_users_list:
        redis_users = users
        users = [user for user in redis_users if user.username in enm_users_list]
        missing_users = set([user.username for user in redis_users]).difference([user.username for user in users])
        for user in missing_users:
            log.logger.debug("Removing redis key\t{0}...".format("{0}_session".format(user)))
            persistence.remove("{0}_session".format(user))
    return helper.generate_user_info_list(users)


def get_users_with_matching_user_roles(users, user_roles):
    """
    Get list of users having the same set of User Roles matching the provided list

    :param users: List of users
    :type users: list
    :param user_roles: List of user roles
    :type user_roles: str
    :return: List of users with matching roles
    :rtype: list
    """
    user_roles = set(user_roles.split(","))
    users_with_matching_user_roles = []
    for user in users:
        list_of_roles = set([role.name for role in user.roles])
        if not list_of_roles.difference(user_roles) and not user_roles.difference(list_of_roles):
            users_with_matching_user_roles.append(user)
    return users_with_matching_user_roles


def delete_users():
    """
    Route to DELETE user information from the database and ENM

    DELETE /users/delete
    DELETE /users/delete?delete_data  # {"username": "User_01", "profile_name": "Test", "user_roles" : "Role||Role1"}

    :raises HTTPException: 404 raised if GET request fails

    :returns: 200 Response object
    :rtype: `requests.Response`
    """
    log.logger.debug("Deleting users from ENM")
    username, profile_name, user_roles = extract_delete_user_values(request)
    success = True
    func_args = None
    try:
        if username:
            func_ref = delete_user_from_enm_by_username
            func_args = [username]
        elif profile_name:
            if not user_roles:
                DELETION_QUEUE.put_unique(profile_name)
                func_ref = delete_profile_users_from_enm
                func_args = [profile_name]
            else:
                func_ref = helper.delete_users_from_enm_by_usernames
                func_args = [helper.get_enm_users_with_matching_user_roles(profile_name, user_roles)]
        else:
            func_ref = delete_all_users_from_enm

        create_and_start_once_off_background_scheduled_job(
            func_ref, "Function: [{0}] with args: {1}.".format(func_ref.__name__, func_args), log.logger,
            func_args=func_args)
        log.logger.debug("Request successful")
        return get_json_response(success=success, rc=200)
    except Exception as e:
        abort_with_message("Could not delete user(s), error encountered :: {0}.".format(str(e.message)),
                           log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR)


def extract_delete_user_values(delete_request):
    """
    Retrieve the available values from the supplied request object if available

    :param delete_request: Request object to retrieve the available values from the supplied request object if available
    :type delete_request: `request`

    :return: Tuple containing any available values for username, profile name and user roles
    :rtype: tuple
    """
    if delete_request.args.get('delete_data'):
        delete_data = delete_request.args.get('delete_data').encode("utf-8")
        delete_dict = {}
        for _ in delete_data.replace("}", "").replace("{", "").replace("'", "").replace("\"", "").split(','):
            delete_dict[_.split(":")[0].strip()] = _.split(":")[-1].strip()
    else:
        delete_dict = {}
    username = delete_dict.get('username')
    profile_name = delete_dict.get('profile_name')
    user_roles = [role for role in delete_dict.get('user_roles').split("||")] if delete_dict.get('user_roles') else None
    return username, profile_name, user_roles


def create():
    """
    Route to create ENM user(s) via POST request

    POST /users/create

    :raises HTTPException: 404 raised if GET request fails

    :returns: 200 Response object
    :rtype: `requests.Response`
    """
    user_count_threshold_abort_check()
    request_data = request.get_json()
    now = datetime.datetime.now()
    creation_time = now.strftime("%m%d-%H%M%S%f")[0:-4]
    username_prefix = profile_name = request_data.get('username_prefix')
    DELETION_QUEUE.block_until_item_removed(username_prefix, log.logger)
    number_of_users = request_data.get('number_of_users')
    user_roles = request_data.get('user_roles')

    log.logger.debug("Create user(s) with following data: username_prefix: {0}, number_of_users: {1}, user_roles: {2}"
                     .format(username_prefix, number_of_users, user_roles))
    if (username_prefix and number_of_users and user_roles and
            isinstance(number_of_users, int) and isinstance(user_roles, list)):
        username_prefix = "{0}_{1}".format(username_prefix, creation_time)

        try:
            user_roles = helper.create_user_role_objects(user_roles)
            users, _ = execute_create_flow(username_prefix, int(number_of_users), user_roles, profile_name)
            return json.dumps(helper.generate_user_info_list(users))
        except Exception as e:
            message = "Could not create user(s) on ENM due to :: {0}.".format(str(e))
            rc = 500
    else:
        message = ("Bad request. username_prefix: {0}, number_of_users (int): {1}, user_roles (list): {2}"
                   .format(username_prefix, number_of_users, user_roles))
        rc = 400

    log.logger.debug(message)
    abort_with_message(message, log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, http_status_code=rc)


def user_count_threshold_abort_check():
    """
    Aborts create user flow if threshold has reached or exception while checking threshold
    """
    threshold_reached = helper.check_user_count_threshold()
    if threshold_reached:
        message, rc = threshold_reached
        abort_with_message(message, log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, http_status_code=rc)


def execute_create_flow(username_prefix, number_of_users, user_roles, profile_name):
    """
    Create Users Flow

    :param username_prefix: Prefix of Username
    :type username_prefix: str
    :param number_of_users: Number of users to be created
    :type number_of_users: int
    :param user_roles: List of role(s) on ENM
    :type user_roles: list
    :param profile_name: name of the profile
    :type profile_name: str
    :raises RuntimeError: if cannot connect to Redis or cannot create users

    :return: list of created enm_user objects, list of failed enm user objects
    :rtype: tuple
    """

    log.logger.debug("Creating Users")
    try:
        helper.delete_existing_users(profile_name, user_roles)
        users, failed_users = create_users_operation(username_prefix, number_of_users, user_roles)
        for index, user in enumerate(users):
            log.logger.debug("User {0} details: {1}".format(index + 1, user.__dict__))
        profile_total_users = get_users_info("", profile_name, "")
        log.logger.debug("Profile: [{0}]\tTotal users found: [{1}]\tUsers created: [{2}]".format(
            profile_name, len(profile_total_users), len(users)))
        return users, failed_users
    except Exception as e:
        raise RuntimeError("Error in execute_create_flow: {0}".format(e))


def delete_user_from_enm_by_username(username):
    """
    Delete a specific user from ENM

    :param username: Username to use to locate the user object
    :type username: str
    """
    try:
        current_users = helper.get_enm_users_list()
        if username in current_users:
            log.logger.debug("Attempting to delete user {0} from ENM.".format(username))
            user = enm_user_2.User(username=username)
            user.delete(delete_as=get_workload_admin_user())
            log.logger.debug("Completed deletion of user {0}.".format(username))
    except Exception as e:
        log.logger.debug("User not deleted from ENM, error encountered :: {0}".format(str(e)))


def delete_profile_users_from_enm(profile_name):
    """
    Delete all the ENM users who match the supplied profile name

    :param profile_name: ProfileName to use to locate the list of user objects
    :type profile_name: str
    """
    log.logger.debug("Attempting to delete all users belonging to {0} profile from ENM.".format(profile_name))
    delete_profile_users(profile_name)
    DELETION_QUEUE.get_item(profile_name)
    log.logger.debug("Completed {0} users deletion.".format(profile_name))


def delete_all_users_from_enm():
    """
    Delete all users from ENM

    :return: Boolean indicating if the delete operation(s) were a success
    :rtype: bool
    """
    log.logger.debug("Attempting to delete all users from ENM.")
    users = helper.get_enm_users_list()
    success = True
    for user in users:
        if user.lower() in ["administrator", workload_admin_with_hostname()]:
            continue
        try:
            delete_user_from_enm_by_username(user)
        except Exception as e:
            log.logger.debug("Failed to delete user {0}, error encountered {1}.".format(user, str(e)))
            success = False
    return success


def sessions_per_profile():
    """
    Get the number of sessions per profile and top 10 sessions hoarders

    POST /users/sessions

    :returns: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        profiles = request_data.get('profiles')
        profile_sessions, session_hoarders = helper.get_sessions_info(profiles)
        return get_json_response(message={'profile_sessions': profile_sessions, 'session_hoarders': session_hoarders})
    except Exception as e:
        abort_with_message("Could not get information about profile sessions :: {0}.".format(str(e.message)),
                           log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR)
