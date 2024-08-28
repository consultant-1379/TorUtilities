from enmutils.lib import log, timestamp
from enmutils_int.lib.services import service_adaptor
from enmutils_int.lib.services.service_adaptor import print_service_operation_message
from enmutils_int.lib.services.service_values import POST_METHOD
from enmutils_int.lib.status_profile import StatusProfile

SERVICE_NAME = "profilemanager"

SET_STATUS_URL = "profile/status/set"
GET_STATUS_URL = "profile/status"
ADD_EXCEPTION_URL = "profile/exception"
CLEAR_ERRORS_URL = "clear/errors"
CLEAR_PIDS_URL = "clear/pids"
GET_PROFILES_URL = "profiles"
GET_CATEGORIES_URL = "categories"
DESCRIBE_PROFILES_URL = "describe"
EXPORT_PROFILES_URL = "export"
DIFF_PROFILES_URL = "diff"


def can_service_be_used(profile=None):
    """
    Determine if service can be used

    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    :return: Boolean to indicate if service can be used or not
    :rtype: bool
    """
    return service_adaptor.can_service_be_used(SERVICE_NAME, profile)


def set_status(argument_dict):
    """
    Add nodes to the workload pool

    :param argument_dict: Command line arguments received from the workload tool
    :type argument_dict: dict
    """
    name = argument_dict.get('name')
    state = argument_dict.get('state')
    start_time = argument_dict.get('start_time')
    pid = argument_dict.get('pid')
    num_nodes = argument_dict.get('num_nodes')
    schedule = argument_dict.get('schedule')
    priority = argument_dict.get('priority')
    last_run = argument_dict.get('last_run')
    user_count = argument_dict.get('user_count')
    log.logger.debug("Starting status add operation.")
    json_data = {"name": name, "state": state, "start_time": start_time, "pid": pid, "num_nodes": num_nodes,
                 "schedule": schedule, "priority": priority, "last_run": last_run, "user_count": user_count}
    send_request_to_service(POST_METHOD, SET_STATUS_URL, json_data=json_data)


def get_status(argument_dict):
    """
    Add nodes to the workload pool

    :param argument_dict: Command line arguments received from the workload tool
    :type argument_dict: dict

    :returns: List of StatusProfile instances
    :rtype: list
    """
    profiles = argument_dict.get('profiles') if argument_dict.get('profiles') else "None"
    category = argument_dict.get('category') if argument_dict.get('category') else "None"
    json_response = argument_dict.get("json_response")
    log.logger.debug("Starting workload status operation.")
    response = send_request_to_service(POST_METHOD, GET_STATUS_URL, json_data={"profiles": profiles,
                                                                               "category": category})
    if json_response:
        return response.json()
    status_objs = []
    for status_values in response.json():
        status_values['name'] = status_values['NAME'].encode('utf-8')
        log.logger.debug("Creating StatusProfile object from received data for profile: {0}"
                         .format(status_values['name']))
        for _ in ['user_count', 'num_nodes']:
            if _ in status_values.keys():
                status_values[_] = int(status_values[_])
        del status_values['NAME']
        status_values['start_time'] = timestamp.convert_str_to_datetime_object(status_values['start_time'])
        status_values['last_run'] = timestamp.convert_str_to_datetime_object(status_values['last_run'])
        status_objs.append(StatusProfile(**status_values))
    log.logger.debug("Found total [{0}] status objects matching request.".format(len(status_objs)))
    return status_objs


def add_profile_exception(argument_dict):
    """
    Add profile Error or Warning as exception to profile

    :param argument_dict: Command line arguments received from the workload tool
    :type argument_dict: dict
    """
    log.logger.debug("Starting exception add operation.")
    send_request_to_service(POST_METHOD, ADD_EXCEPTION_URL, json_data=argument_dict)


def get_categories_list():
    """
    Get the list of all profile categories.
    """
    log.logger.debug("Starting retrieval of categories list.")
    print_service_operation_message(send_request_to_service(POST_METHOD, GET_CATEGORIES_URL, retry=False), log.logger)


def clear_profile_exceptions(profile_names=None):
    """
    Add profile Error or Warning as exception to profile

    :param profile_names: List of profile names
    :type profile_names: list
    """

    log.logger.debug("Starting clear errors operation.")
    json_data = {"profile_names": profile_names if profile_names else "None"}
    print_service_operation_message(send_request_to_service(
        POST_METHOD, CLEAR_ERRORS_URL, json_data=json_data, retry=False), log.logger)


def get_all_profiles_list():
    """
    Get the list of all profiles
    """
    log.logger.debug("Starting retrieval of profiles list.")
    print_service_operation_message(send_request_to_service(POST_METHOD, GET_PROFILES_URL, retry=False), log.logger)


def clear_profile_pid_files(profile_names):
    """
    Remove the supplied profile name PID files if present on the filesystem

    :param profile_names: List of profile names
    :type profile_names: list
    """

    log.logger.debug("Starting clear PID File operation.")
    print_service_operation_message(send_request_to_service(POST_METHOD, CLEAR_PIDS_URL,
                                                            json_data={"profile_names": profile_names}, retry=False),
                                    log.logger)


def describe_profiles(profile_names):
    """
    Retrieve the describe information for the supplied profile names

    :param profile_names: List of profile names
    :type profile_names: list
    """
    log.logger.debug("Starting describe profile(s) operation.")
    print_service_operation_message(send_request_to_service(POST_METHOD, DESCRIBE_PROFILES_URL,
                                                            json_data={"profile_names": profile_names}, retry=False),
                                    log.logger)


def export_profiles(profiles_to_export, export_file_path, categories_to_export=None, all_profiles=False,
                    all_categories=False):
    """
    Export the supplied profile objects to file

    :param profiles_to_export: List of profile names
    :type profiles_to_export: list
    :param export_file_path: The file path to be used for the exported file
    :type export_file_path: str
    :param categories_to_export: Dictionary containing key value pairs of profile name, profile names by category
    :type categories_to_export: dict
    :param all_profiles: Boolean indicating if all profiles should be exported
    :type all_profiles: bool
    :param all_categories: Boolean indicating if all categories should be exported
    :type all_categories: bool
    """
    log.logger.debug("Starting retrieval of profiles list.")
    json_data = {
        "profiles_to_export": profiles_to_export,
        "export_file_path": export_file_path,
        "categories_to_export": categories_to_export if categories_to_export else "None",
        "all_profiles": all_profiles if all_profiles else "None",
        "all_categories": all_categories if all_categories else "None"
    }
    print_service_operation_message(send_request_to_service(POST_METHOD, EXPORT_PROFILES_URL, json_data=json_data,
                                                            retry=False), log.logger)


def diff_profiles(**kwargs):
    """
    Retrieve the diff information for the supplied profile names

    :param kwargs: Dict of parameters
    :type kwargs: dict
    """
    log.logger.debug("Starting diff profile(s) operation.")
    print_service_operation_message(send_request_to_service(POST_METHOD, DIFF_PROFILES_URL,
                                                            json_data={"diff_parameters": kwargs}, retry=False),
                                    log.logger)


def send_request_to_service(method, url, json_data=None, retry=True):
    """
    Send REST request to ProfileManager service

    :param method: Method to be used
    :type method: method
    :param url: Destination URL of request
    :type url: str
    :param json_data: Optional json data to be send as part of request
    :type json_data: dict
    :param retry: Boolean indicating if the REST request should be retired if unsuccessful
    :type retry: bool

    :return: Response from ProfileManager service
    :rtype: `requests.Response`

    :raises EnvironError: if error thrown in RESt request or if response is bad
    """

    response = service_adaptor.send_request_to_service(method, url, SERVICE_NAME, json_data=json_data, retry=retry)
    return response
