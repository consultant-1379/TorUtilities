import datetime
import json
import os
import re
import threading

from flask import Blueprint, request

from enmutils.lib import persistence, log, timestamp, config
from enmutils_int.lib.load_mgr import clear_profile_errors, get_persisted_profiles_by_name
from enmutils_int.lib.services.profilemanager_helper_methods import diff_profiles, get_all_profile_names, get_categories
from enmutils_int.lib.services.profilemanager_monitor import verify_profile_state
from enmutils_int.lib.services.service_common_utils import (get_json_response, abort_with_message,
                                                            create_and_start_background_scheduled_job,
                                                            create_and_start_once_off_background_scheduled_job)
from enmutils_int.lib.services.service_values import URL_PREFIX
from enmutils_int.lib.status_profile import StatusProfile, UNWANTED_GLOBAL_ITEMS
from enmutils_int.lib.workload_network_manager import get_all_networks

SERVICE_NAME = "profilemanager"
TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
EXPORT_PROP_FILE_NAME = "_prop_" + TIMESTAMP + ".py"

application_blueprint = Blueprint(SERVICE_NAME, __name__, url_prefix=URL_PREFIX)

TERE_LINK = "https://eteamspace.internal.ericsson.com/pages/viewpage.action?pageId=1982554551"
SCHEDULER_INTERVAL_MINS = 60
CONSISTENTLY_DEAD_PROFILES = []
DEAD_PROFILES = {}
VERIFICATION_KEY = "profile-check-key"


def at_startup():
    """
    Start up function to be executed when service is created
    """
    log.logger.debug("Running startup functions.")
    create_and_start_once_off_background_scheduled_job(once_off_function_holder,
                                                       "{0}_VERIFY_PROFILE_ONCE_OFF".format(SERVICE_NAME), log.logger)
    create_and_start_background_scheduled_job(verify_profiles, SCHEDULER_INTERVAL_MINS * 4,
                                              "{0}_VERIFY_PROFILE_FOUR_HOURLY".format(SERVICE_NAME), log.logger)
    log.logger.debug("Startup complete")


def once_off_function_holder():
    """
    Single function to pass to background scheduler
    """
    for func in [persisted_verify_key, verify_profiles]:
        try:
            log.logger.debug("# Starting function: {0}".format(str(func.func_name)))
            func()
            log.logger.debug("# Function complete: {0}".format(str(func.func_name)))
        except Exception as e:
            log.logger.debug(str(e))


def persisted_verify_key(remove_key=True):
    """
    Optional remove and return persisted key to enable/disable profile verification check

    :param remove_key: Boolean indicating if the key should be removed or not
    :type remove_key: bool

    :return: Persisted key value
    :rtype: str
    """
    msg = ("Checking persistence for verify key" if not remove_key else
           "Removing verify key from persistence if persisted.")
    log.logger.debug(msg)
    if remove_key:
        persistence.remove(VERIFICATION_KEY)
    return persistence.get(VERIFICATION_KEY)


def status():
    """
    Route to POST to retrieve workload status objects

    POST /profile/status

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        profile_list = request_data.get('profiles') if request_data and request_data.get('profiles') != "None" else None
        profile_name = profile_list[0] if profile_list and len(profile_list) == 1 else None
        profile_list = None if profile_name else profile_list
        category = request_data.get('category') if request_data and request_data.get('category') != "None" else None

        profile_status = get_status(profile_name=profile_name, profile_list=profile_list, categories=category) or []
        json_status_objs = []
        for _ in profile_status:
            if hasattr(_, '__dict__'):
                prof_status = _.status
                status_values = _.__dict__
                status_values["start_time"] = timestamp.convert_datetime_to_str_format(status_values["start_time"])
                status_values["last_run"] = timestamp.convert_datetime_to_str_format(status_values["last_run"])
                status_values["status"] = prof_status
                json_status_objs.append(status_values)
        return json.dumps(json_status_objs)
    except Exception as e:
        abort_with_message("Failed to retrieve Status values.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def set_status():
    """
    Route to POST to set workload status object

    POST /profile/status/set

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        request_data['start_time'] = timestamp.convert_str_to_datetime_object(request_data['start_time'])
        request_data['last_run'] = timestamp.convert_str_to_datetime_object(request_data['last_run'])
        prof = StatusProfile(**request_data)
        persistence.set('{0}-status'.format(prof.NAME), prof, -1)
        log.logger.debug("Successfully set status for \t{0}".format(prof.NAME))
        return get_json_response()
    except Exception as e:
        abort_with_message("Failed to set Profile Status.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def set_error_or_warning():
    """
    Route to POST to set workload exception object

    POST /profile/exception

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        profile_key = request_data.get("profile_key")
        profile_values = request_data.get("profile_values")
        persistence.set(profile_key.encode('utf-8'), profile_values, -1, log_values=False)
        log.logger.debug("Successfully add exception to \t{0}".format(profile_key.split("-")[0]))
        return get_json_response()
    except Exception as e:
        abort_with_message("Failed to add Profile Exception.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def categories_list():
    """
    Route to POST list of all Profile Categories.

    POST /categories

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        message = log.green_text("Categories:\n{0}".format(", ".join(get_categories())))
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Failed to retrieve categories list.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def clear_errors():
    """
    Route to POST to clear Profile(s) errors

    POST /clear/errors

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        profile_names = ([profile_name.encode('utf-8') for profile_name in request_data.get("profile_names")] if
                         request_data.get("profile_names") != "None" else None)
        clear_profile_errors(profile_names=profile_names)
        msg_stub = "all active profiles." if not profile_names else "profile(s):: [{0}]".format(
            ", ".join(profile_names))
        message = "\nSuccessfuly removed errors and warnings for {0}".format(msg_stub)
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Failed to remove profile errors from persistence.", log.logger, SERVICE_NAME,
                           log.SERVICES_LOG_DIR, e)


def clear_pids():
    """
    Route to POST to clear Profile(s) pid file(s)

    POST /clear/pids

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        request_data = request.get_json()
        profile_names = [profile_name.encode('utf-8') for profile_name in request_data.get("profile_names")]
        message = delete_pid_files(profile_names=profile_names)
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Failed to remove profile pid files.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def profiles_list():
    """
    Route to POST list of all Profiles.

    POST /profiles

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        message = log.cyan_text("Existing Profiles:") + log.green_text("\n{0}".format(
            ", ".join([profile.upper() for profile in get_all_profile_names()])))
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Failed to retrieve profiles list.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def describe():
    """
    Route to POST describe of Profile(s).

    POST /describe

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        message = "\n".join(build_describe_message_for_profiles(request.get_json().get('profile_names')))
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Unable to retrieve describe information.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR,
                           e)


def get_status(profile_name=None, profile_list=None, categories=None):
    """
    Get the workload status objects

    :param profile_name: Profile name which corresponds to supported workload profiles
    :type profile_name: str
    :param profile_list: List of profile names which correspond to supported workload profiles
    :type profile_list: list
    :param categories: List of category which correspond to supported workload categories
    :type categories: list

    :return: List of profile status objects
    :rtype: list
    """
    if profile_name:
        return [get_profile_status(profile_name)]
    elif profile_list:
        return get_multiple_status(profile_list)
    elif categories:
        return get_profiles_by_category(categories)
    else:
        status_keys = [key for key in persistence.get_all_default_keys() if key.endswith("-status")]
        return persistence.get_key_values_from_default_db(status_keys)


def get_profile_status(profile_name):
    """
    Get the profile status of the supplied status

    :param profile_name: Name of the profile to retrieve the status
    :type profile_name: str

    :return: List containing the profile status object
    :rtype: list
    """
    return persistence.get("{0}-status".format(profile_name))


def get_multiple_status(profiles):
    """
    Get status of multiple profiles

    :param profiles: List of names of the profiles to retrieve the status
    :type profiles: list

    :return: List containing the profile status objects
    :rtype: list
    """
    profile_keys = ["{0}-status".format(profile) for profile in profiles]
    return persistence.get_key_values_from_default_db(profile_keys)


def get_profiles_by_category(categories):
    """
    Get the list of profiles which belong to a particular category

    :param categories: List of profile categories
    :type categories: list

    :return: List containing all of the profiles of a specific category
    :rtype: list
    """
    keys = persistence.get_all_default_keys()
    status_keys = []
    for key in keys:
        for category in categories:
            if key.startswith(category) and key.endswith("-status") and key not in status_keys:
                status_keys.append(key)
    return persistence.get_key_values_from_default_db(status_keys)


def delete_pid_files(profile_names):
    """
    Delete the pid files for the supplied profile names if they exist

    :param profile_names: List of profile names, delete the pid files for the supplied profile names if they exist.
    :type profile_names: list

    :returns: Message containing details of the pid files removed
    :rtype: str
    """
    message = ""
    for profile in profile_names:
        pidfile = os.path.join("/var/tmp/enmutils/daemon", "{0}.pid".format(profile.encode('utf-8').upper()))
        if os.path.exists(pidfile):
            os.remove(pidfile)
            base_message = log.green_text('Successfully deleted pid for {0}.\n'.format(profile))

        else:
            base_message = log.green_text('No pid file found for {0}, nothing to delete.\n'.format(profile))
        message += base_message
        log.logger.info(base_message)
    return message


def export():
    """
    Route to POST to export Profile(s) file(s)

    POST /export

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """

    request_data = request.get_json()
    try:
        profiles_to_export = {profile.NAME: profile for profile in
                              persistence.get_keys(request_data["profiles_to_export"])}

        categories_to_export = ({key: persistence.get_keys(value) for key, value in
                                 request_data["categories_to_export"].items()} if
                                request_data["categories_to_export"] != "None" else None)
        export_file_path = str(request_data["export_file_path"])
        all_profiles = True if request_data["all_profiles"] != "None" else None
        all_categories = True if request_data["all_categories"] != "None" else None
        message = generate_export_file(profiles_to_export, export_file_path, categories_to_export=categories_to_export,
                                       all_profiles=all_profiles, all_categories=all_categories)
        return get_json_response(message=message)
    except Exception as e:
        abort_with_message("Failed to export profile(s) attributes.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def build_describe_message_for_profiles(profile_names):
    """
    Call the describe functions and build up the complete message

    :param profile_names: List of profile names to describe
    :type profile_names: list

    :return: List of constructed profile describe messages
    :rtype: list
    """
    messages = []
    for profile_name in profile_names:
        primary_message = print_profile_description(profile_name)
        secondary_message = print_basic_network_values(profile_name)
        messages.append(primary_message + secondary_message)
    return messages


def print_profile_description(profile_name):
    """
    Print a link to the latest ENM TERE in order to find profile description.

    :param profile_name: name of the profile
    :type profile_name: str

    :returns: Link to the latest ENM TERE
    :rtype: str
    """
    primary_message = '\n Description of the profile: {0}: \n'.format(profile_name.upper())
    log.logger.info(log.cyan_text(primary_message))
    secondary_message = "\n Please refer to the latest ENM TERE at: \n {0} \n ".format(TERE_LINK)
    log.logger.info(secondary_message)
    return log.cyan_text(primary_message) + secondary_message


def print_basic_network_values(profile_name):
    """
    Print the profile values from basic_network.py

    :param profile_name: name of the profile to print the basic network values of
    :type profile_name: str

    :returns: Basic network values of the matching profile
    :rtype: str
    """
    basic_network_dict = get_all_networks().get('basic')
    application = re.split(r'_[0-9]', profile_name.lower())[0].replace('_setup', '')
    profile_basic_network_values = basic_network_dict.get(application).get(profile_name.upper())
    primary_message = '\n Basic network values for {0}: \n'.format(profile_name.upper())
    log.logger.info(log.cyan_text(primary_message))
    secondary_message = '{0}\n'.format(profile_basic_network_values)
    log.logger.info(secondary_message)
    return log.cyan_text(primary_message) + secondary_message


def generate_export_file(profiles_to_export, export_file_path, categories_to_export=None, all_profiles=False,
                         all_categories=False):
    """
    Exports profile class properties in to a file in the format profile_name_prop_timestamp.py or
    category_prop_timestamp.py in the present working directory

    :param profiles_to_export: Dict containing key, value pairs profile name and list of profile objects
    :type profiles_to_export: dict
    :param export_file_path: File path of the exported file
    :type export_file_path: str
    :param categories_to_export: Dict containing key, value pairs categories and list of profile objects
    :type categories_to_export: dict or None
    :param all_profiles: Boolean indicating if all profiles should be exported
    :type all_profiles: bool
    :param all_categories: Boolean indicating if all categories should be exported
    :type all_categories: bool

    :returns: File path of the export file
    :rtype: str
    """
    profile_ids = []
    file_list = []
    category_ids = []
    if all_profiles or all_categories:
        profiles_to_export = profiles_to_export if not categories_to_export else categories_to_export
        export_path = export_all(profiles_to_export, export_file_path, all_profiles=all_profiles)
    elif not categories_to_export:
        profile_dict = get_profiles_and_file_names(profiles_to_export)
        for filename, profile_list in profile_dict.items():
            write_to_file(profile_list, filename, export_file_path)
            for profile in profile_list:
                profile_ids.append(profile.NAME)
            file_list.append(filename)
        export_path = print_export_path(file_list, profile_ids, "profile", export_file_path)

    else:
        for category_name, profiles in categories_to_export.items():
            filename = category_name.lower() + EXPORT_PROP_FILE_NAME
            write_to_file(profiles, filename, export_file_path)
            category_ids.append(category_name)
            file_list.append(filename)
        export_path = print_export_path(file_list, category_ids, "category", export_file_path)
    return export_path


def write_to_file(profiles, filename, export_file_path):
    """
    This method will open a file with given name and write the properties of the profile in to it.

    :param profiles: list of profile objects
    :type profiles: list
    :param filename: file name to which the properties of the given profiles will be written to
    :type filename: str
    :param export_file_path: File path of the exported file
    :type export_file_path: str
    """
    absolute_file_path = os.path.join(export_file_path, filename)
    with open(absolute_file_path, "w") as config_file:
        config_file.write("import datetime\n\n")
        profiles.sort()
        for profile in profiles:
            if profile.EXPORTABLE:
                config_file.write("{0} = {{\n".format(profile))
                for item in [item for item in dir(profile) if item.isupper() and item not in UNWANTED_GLOBAL_ITEMS]:
                    if isinstance(profile.__getattribute__(item), str):
                        config_file.write("    '{0}': '{1}',\n".format(item, profile.__getattribute__(item)))
                    else:
                        config_file.write("    '{0}': {1},\n".format(item, profile.__getattribute__(item)))
                config_file.write("}\n\n")


def get_profiles_and_file_names(profiles_to_export):
    """
    This method is used to get the file name from the profile names
    Ex : for FM_01 and FM_02 profiles, file name would start with fm_prop_xxxx and vice versa

    :param profiles_to_export: Dict containing key, value pairs profile name and list of profile objects
    :type profiles_to_export: dict

    :returns: dict of file name and profile objects
    :rtype: dict
    """
    i = 0
    multiple_profiles = {}
    profile_names = profiles_to_export.keys()
    while i < len(profile_names):
        first_profile = profile_names[i]
        app = first_profile.split("_")[0]
        profiles_of_same_app = [profile_name for profile_name in profile_names if
                                app == profile_name.split("_")[0] and profile_name not in first_profile]
        if profiles_of_same_app:
            profiles_of_same_app.append(first_profile)
            for profile in profiles_of_same_app:
                profile_names.remove(profile)
            file_name = '{0}{1}'.format(app.lower(), EXPORT_PROP_FILE_NAME)
            profile_obj_list = [profile_obj for app_profile in profiles_of_same_app for profile, profile_obj in
                                profiles_to_export.items() if app_profile == profile]
            multiple_profiles[file_name] = profile_obj_list
        else:
            profile_names.remove(first_profile)
            file_name = first_profile.lower() + EXPORT_PROP_FILE_NAME
            multiple_profiles[file_name] = [profiles_to_export[first_profile]]
    return multiple_profiles


def print_export_path(file_list, export_ids, type_of_export, export_file_path):
    """
    Logs the export path of the exported files

    :param file_list: A list of names for all files to be exported
    :type file_list: list
    :param export_ids: A list of ids for all file to be exported
    :type export_ids: list
    :param type_of_export: Type of export
    :type type_of_export: string
    :param export_file_path: File path of the exported file
    :type export_file_path: str

    :returns: File path of the export file(s)
    :rtype: str
    """
    export_paths = []
    for index, file_name in enumerate(file_list):
        file_name = str(file_name).strip("[]'")
        export_paths.append("{0} {1} properties exported to {2}".format(export_ids[index], type_of_export,
                                                                        os.path.join(export_file_path, file_name)))
    log.logger.info("\n".join(export_paths))
    return "\n".join(export_paths)


def export_all(profiles_to_export, export_file_path, all_profiles=False):
    """
    Exports all the active profile properties in to file named all_profiles if no category is mentioned
    and all_categories if category is mentioned by the user

    :param profiles_to_export: Dict containing key, value pairs profile name| category and list of profile objects
    :type profiles_to_export: dict
    :param export_file_path: File path of the exported file
    :type export_file_path: str
    :param all_profiles: Boolean indicating if all profiles or all categories should be exported
    :type all_profiles: bool

    :returns: File path of the export file
    :rtype: str
    """

    if all_profiles:
        filename = 'all_profiles' + EXPORT_PROP_FILE_NAME
        msg = "All profiles properties"
    else:
        filename = 'all_categories' + EXPORT_PROP_FILE_NAME
        msg = "All profiles properties from all categories"
    profile_objs = profiles_to_export.values()
    write_to_file(profile_objs, filename, export_file_path=export_file_path)
    export_path = "{0} exported to '{1}' in {2} directory.".format(msg, filename, export_file_path)
    log.logger.info(export_path)
    return export_path


def diff():
    """
    Route to POST diff of Profile(s).

    POST /diff

    :raises HTTPException: 500 raised if POST request fails

    :return: 200 Response object
    :rtype: `requests.Response`
    """
    try:
        parameters = request.get_json().get('diff_parameters')
        config.set_prop("print_color", str(not parameters.get('no_ansi')))
        message = "\n".join(diff_profiles(**parameters))
        config.set_prop("print_color", 'False')
        return get_json_response(message=message)
    except RuntimeError as e:
        return get_json_response(message=e.message, rc=599)
    except Exception as e:
        abort_with_message("Unable to retrieve diff information.", log.logger, SERVICE_NAME, log.SERVICES_LOG_DIR, e)


def verify_profiles():
    """
    Verify profiles are in the expected state
    """
    try:
        threading.current_thread().name = "ProfileMonitor"
        persisted_key_value = persisted_verify_key(remove_key=False)
        if persisted_key_value:
            log.logger.debug("Verification currently disabled, no checks will be performed.")
            return
        log.logger.debug("Starting verification of active profiles.")
        profile_objects = [value for value in get_persisted_profiles_by_name().values()]
        profiles_to_verify = [profile for profile in profile_objects if profile.NAME not in CONSISTENTLY_DEAD_PROFILES]
        if profiles_to_verify:
            dead_or_inactive_profiles_found = verify_profile_state(profiles_to_verify)
            if dead_or_inactive_profiles_found:
                start_time_dict = {profile.NAME: profile.start_time for profile in profile_objects if
                                   profile.NAME in dead_or_inactive_profiles_found}
                check_for_consistently_dead_or_inactive_profiles(dead_or_inactive_profiles_found, start_time_dict)
        log.logger.debug("Completed verification of active profiles.")
    except Exception as e:
        log.logger.debug("Failed to start verification of profiles, error encountered: [{0}]".format(str(e)))


def check_for_consistently_dead_or_inactive_profiles(dead_or_inactive_profiles_found, profile_start_times):
    """
    Check if the profile has been DEAD on a previous check and increment times DEAD or add to the consistently dead list

    :param dead_or_inactive_profiles_found: List of profiles which have been identified as dead or inactive
    :type dead_or_inactive_profiles_found: list
    :param profile_start_times: Dictionary containing key,value pairs profile Name, profile start time
    :type profile_start_times: dict
    """
    global CONSISTENTLY_DEAD_PROFILES, DEAD_PROFILES
    CONSISTENTLY_DEAD_PROFILES = []
    DEAD_PROFILES = {profile_name: profile_count for profile_name, profile_count in DEAD_PROFILES.items()
                     if profile_name in dead_or_inactive_profiles_found}
    reset_recently_restarted_profiles_dead_count(dead_or_inactive_profiles_found, profile_start_times)
    for profile in dead_or_inactive_profiles_found:
        if profile not in DEAD_PROFILES.keys():
            DEAD_PROFILES[profile] = 1
        elif DEAD_PROFILES.get(profile) >= 3 and profile not in CONSISTENTLY_DEAD_PROFILES:
            CONSISTENTLY_DEAD_PROFILES.append(profile)
        else:
            DEAD_PROFILES[profile] += 1


def reset_recently_restarted_profiles_dead_count(profiles, profile_start_times):
    """
    Check if the start time is available for any identified profiles and reset if running less than 4 hours

    :param profiles: List of profiles identified
    :type profiles: list
    :param profile_start_times: Dictionary containing key,value pairs profile Name, profile start time
    :type profile_start_times: dict
    """
    log.logger.debug("Checking if inactive profile was active less than four hours.")
    now = datetime.datetime.now()
    for profile in profiles:
        profile_time = profile_start_times.get(profile.upper())
        if getattr(profile_time, 'now', None):
            updated_time = profile_time.replace(year=now.year)
            if (now - updated_time).total_seconds() <= 14400:
                log.logger.debug("Inactive profile is active less than four hours.")
                global DEAD_PROFILES
                DEAD_PROFILES[profile] = 0
        else:
            log.logger.debug("Start time is not in correct format to verify.")
