import re
from operator import attrgetter
from collections import Counter
from tabulate import tabulate

from enmutils.lib import log, config
from enmutils.lib.arguments import is_valid_version_number
from enmutils.lib.enm_node_management import CmManagement
from enmutils.lib import enm_user_2
from enmutils_int.lib.common_utils import return_dict_from_json_artifact, get_installed_version
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.load_mgr import (get_updated_active_profiles, get_all_active_profiles, _get_profile,
                                       get_persisted_profiles_by_name, INT_PACKAGE, IGNORE_PROFILES)
from enmutils_int.lib.nexus import check_nexus_version
from enmutils_int.lib.services import deployment_info_helper_methods
from enmutils_int.lib.workload_network_manager import get_all_networks
from enmutils_int.lib import node_pool_mgr


INVALID_VERSION_MESSAGE = "invalid_version"
INVALID_NETWORK_MESSAGE = "invalid_network"


def update_message(message):
    """
    Update the message to be displayed

    :param message: Diff message to be displayed
    :type message: str

    :return: Updated message to be displayed
    :rtype: str
    """
    additional_message = ""
    if config.has_prop(INVALID_VERSION_MESSAGE):
        additional_message += config.get_prop(INVALID_VERSION_MESSAGE)
    if config.has_prop(INVALID_NETWORK_MESSAGE):
        additional_message += config.get_prop(INVALID_NETWORK_MESSAGE)
    config.set_prop(INVALID_VERSION_MESSAGE, "")
    config.set_prop(INVALID_NETWORK_MESSAGE, "")
    return additional_message + message


def diff_profiles(**parameters):
    """
    Perform workload diff operation.

    :param parameters: Dictionary of keyword arguments
    :type parameters: dict
    :return: List of strings
    :rtype: str
    :raises RuntimeError: if no differences found
    """
    ignore = IGNORE_PROFILES
    updated = parameters.get("updated", False)
    version = parameters.get("version", "")
    priority = parameters.get("priority", 0)
    list_format = parameters.get("list_format", False)
    profile_names = parameters.get("profile_names", [])
    wl_enm_nodes_diff = parameters.get("wl_enm_nodes_diff", [])
    wl_enm_poids_diff = parameters.get("wl_enm_poids_diff", [])

    log.logger.debug("Performing workload diff operation")
    if wl_enm_nodes_diff:
        messages = get_difference_nodes_between_wlvm_and_enm()
    elif wl_enm_poids_diff:
        messages = get_wl_poids()
    else:
        supported_profiles = get_all_profile_names()

        active_profiles = get_list_of_active_profiles_names()
        installed_version = get_installed_version(INT_PACKAGE)

        if updated:
            messages = print_profiles_to_restart(active_profiles, list_format, installed_version)
        else:
            messages = print_profiles_diff(profile_names, supported_profiles, list_format, version, priority, ignore,
                                           installed_version)

    log.logger.debug("Workload diff operation complete")
    return messages


def get_list_of_active_profiles_names():
    """
    Gets the list of active_profiles by name
    :return: List of active profile names
    :rtype: list
    """

    profile_objects = get_persisted_profiles_by_name(diff=True)

    active_profile_names = [profile_name for profile_name, profile in profile_objects.iteritems() if profile]

    return active_profile_names


def get_data_for_profiles_to_restart(updated_profiles):
    """
    Get information about profiles to be restarted

    :param updated_profiles: List of the profile objects which have been updated
    :type updated_profiles: list

    :return: Information about profiles to be restarted
    :rtype: list
    """
    profiles_data = []

    for profile in updated_profiles:
        profile_version_running = getattr(profile, "version", "N/A")
        start_time = profile.start_time.strftime("%d-%m-%Y") if getattr(profile, "start_time", None) else "N/A"
        profile_info = [log.cyan_text(profile.NAME), profile_version_running, start_time, log.green_text("YES")]
        profiles_data.append(profile_info)

    return profiles_data


def print_profiles_to_restart(active_profiles, list_format, installed_version):
    """
    Print info on profiles mainly around whether or not they should be restarted

    :param active_profiles: List of active profiles
    :type active_profiles: list
    :param list_format: Boolean to indicate if output should be in list format
    :type list_format: bool
    :param installed_version: Installed version of the RPM
    :type installed_version: str
    :return: List of strings
    :rtype: str
    """
    if not active_profiles:
        message = log.green_text('No profiles to be restarted. No active profiles found.')
        log.logger.info(message)
        return [message]

    updated_profiles = get_updated_active_profiles()

    if list_format:
        message1 = "List of profiles:"
        log.logger.info(message1)
        message2 = " ".join(sorted([profile.NAME for profile in updated_profiles]))
        log.logger.info(message2)
        return [message1, message2]

    message1 = log.purple_text("Locally installed version: {0}".format(log.green_text(installed_version)))
    log.logger.info(message1)

    tabulate_data = get_data_for_profiles_to_restart(updated_profiles)

    if tabulate_data:
        message2 = tabulate(
            sorted(tabulate_data),
            headers=[
                log.blue_text('Profile'),
                log.blue_text('Running Version'),
                log.blue_text('Start date'),
                log.blue_text('Restart Required')])
        log.logger.info(message2)

    else:
        message2 = log.green_text('No profiles to be restarted. All active profiles already on latest update.')
        log.logger.info(message2)

    return [message1, message2]


def print_profiles_diff(profile_names, supported_profiles, list_format, version, priority, ignore, installed_version):
    """
    Get and Display profiles information regarding: running, supported states, opened jira's.
    If version provided it will attempt to download data from Nexus, otherwise - will query the system dynamically

    :param profile_names: List of profile names
    :type profile_names: list
    :param supported_profiles: List of supported profiles
    :type supported_profiles: list
    :param list_format: Boolean to indicate if list format is to be used
    :type list_format: bool
    :param version: Version of RPM to check against
    :type version: str
    :param priority: Priority of profile
    :type priority: int
    :param ignore: List if ignored profile names
    :type ignore: list
    :param installed_version: Version of RPM installed
    :type installed_version: str
    :return: List of strings
    :rtype: list
    :raises RuntimeError: if no differences reported
    """
    internal_package = "int"
    profile_names = profile_names or supported_profiles
    profile_names = [profile_name.upper() for profile_name in profile_names]
    running_profiles, not_running_profiles = get_running_not_running_profiles(profile_names, priority, ignore,
                                                                              installed_version)

    if list_format:
        message1 = "List of profiles:"
        log.logger.info(message1)
        message2 = " ".join(sorted([profile.NAME for profile in running_profiles + not_running_profiles]))
        log.logger.info(message2)
        return [message1, message2]

    if version:
        if version.upper() == 'LATEST' or is_valid_version_number(version):
            # Download json with information for provided version of profiles
            version = check_nexus_version(internal_package, version)
        else:
            invalid_version_message = log.red_text('Invalid version provided: {0}\n'.format(version))
            config.set_prop(INVALID_VERSION_MESSAGE, invalid_version_message)
            log.logger.info(invalid_version_message)
            version = None

    artifact_profiles, profile_values_local = get_profiles_info_for_specific_version(version, profile_names)

    tabulate_data = set_tabulated_info([], running_profiles, profile_values_local, ignore,
                                       artifact_profiles if artifact_profiles else False)
    tabulate_data = set_tabulated_info(tabulate_data, not_running_profiles, profile_values_local, ignore,
                                       artifact_profiles if artifact_profiles else False, running=False)

    if tabulate_data:
        if artifact_profiles:
            message1 = tabulate(
                sorted(tabulate_data),
                headers=[
                    log.blue_text('Profile'),
                    log.blue_text('Running'),
                    log.blue_text('Priority'),
                    log.blue_text('Supported local'),
                    log.blue_text('Supported nexus ({0})'.format(version)),
                    log.blue_text('Physical Supported'),
                    log.blue_text('Cloud Supported'),
                    log.blue_text('CN Supported'),
                    log.blue_text('Note')], tablefmt="plain")
            log.logger.info(message1)

        else:
            message1 = tabulate(
                sorted(tabulate_data),
                headers=[
                    log.blue_text('Profile'),
                    log.blue_text('Running'),
                    log.blue_text('Priority'),
                    log.blue_text('Supported local'),
                    log.blue_text('Physical Supported'),
                    log.blue_text('Cloud Supported'),
                    log.blue_text('CN Supported'),
                    log.blue_text('Note')], tablefmt="plain")
            log.logger.info(message1)

        message2 = ("\nYou can start the non running supported profiles using "
                    "/opt/ericsson/enmutils/bin/workload start all\n")
        log.logger.info(log.yellow_text(message2))
        message1 = update_message(message1)
        return [message1, message2]

    else:
        raise RuntimeError("No 'diff' information to display for the profiles provided")


def get_running_not_running_profiles(profile_names, priority, ignore, installed_version):
    """
    Get running and not running profile objects based on data in persistence

    :param profile_names: List of Profile names
    :type profile_names: list
    :param priority: Priority of profile
    :type priority: int
    :param ignore: List of profile names to ignore
    :type ignore: list
    :param installed_version: Version of RPM installed
    :type installed_version: str
    :return: tuple of lists of profiles running and not running
    :rtype: tuple
    """
    running = get_all_active_profiles(profile_names, diff=True)
    not_running = {profile_name: _get_profile(profile_name) for profile_name in profile_names if
                   profile_name not in running}

    running_profiles = running.values()
    not_running_profiles = not_running.values()

    if priority:
        running_profiles, not_running_profiles = get_profiles_info_for_specified_priority(
            running_profiles, not_running_profiles, priority, ignore, installed_version)

    return running_profiles, not_running_profiles


def get_profiles_info_for_specified_priority(running, not_running, priority, ignore, installed_version):
    """
    Returns only the profiles that have the priority specified

    :type running: list
    :param running: profile objects that are running
    :type not_running: list
    :param not_running: profile objects that are not running
    :type priority: int
    :param priority: the priority rating specified
    :rtype: list
    :param ignore: List of profile names to ignore
    :type ignore: list
    :param installed_version: Version of RPM installed
    :type installed_version: str
    :return: tuple of lists of running profile objects that are of the priority specified and those that are not
    :rtype: tuple
    """
    def get_profiles_with_priority(profiles, json_dict_data):
        priority_profiles = []
        for profile in profiles:
            if profile.NAME in ignore:
                continue
            app = re.split(r'_[0-9]', profile.NAME.lower())[0].replace('_setup', '')
            if not json_dict_data.get('basic').get(app):
                log.logger.info("Application not found {0}, may not be available in this rpm.".format(app))
                continue
            if not json_dict_data.get('basic').get(app).get(profile.NAME.upper()):
                log.logger.info("Profile not found {0}, may not be available in this rpm."
                                .format(profile.NAME.upper()))
                continue
            if int(priority) == json_dict_data.get('basic').get(app).get(profile.NAME.upper()).get('PRIORITY'):
                priority_profiles.append(profile)
        return priority_profiles

    json_dict = return_dict_from_json_artifact(installed_version)

    running_profiles_with_priority = get_profiles_with_priority(running, json_dict)
    not_running_profiles_with_priority = get_profiles_with_priority(not_running, json_dict)

    log.logger.debug("Number of Profiles with priority {0}:- Running: {1} Not Running: {2}"
                     .format(priority, len(running_profiles_with_priority), len(not_running_profiles_with_priority)))

    return running_profiles_with_priority, not_running_profiles_with_priority


def get_profiles_info_for_specific_version(version, profile_names):
    """
    Returns supported and not supported profiles for a specific version of released rpm
    for a particular network
    :param version: Version of RPM in question
    :type version: str
    :param profile_names: List of profile names
    :type profile_names: list
    :return: list of supported and not supported profiles
    :return: tuple of dictionaries
             profiles_supported_artifact: dict consisting of profile.NAME as key and dict of profile values as values
                                         for the given rpm version
             profiles_supported_local: dict consisting of profile.NAME as key and dict of profile local values as
                                      values
    :rtype: tuple
    """
    profiles_supported_artifact = []  # downloaded from Nexus
    networks = get_all_networks()
    profiles_supported_local = get_values_for_profile_from_python_dict(networks, "basic", profile_names)

    if version:
        # Convert downloaded json file to dictionary
        fetched_profile_values = return_dict_from_json_artifact(version)

        # Basic configurations fetched are the foundation values
        profiles_supported_artifact = get_values_for_profile_from_python_dict(fetched_profile_values, "basic",
                                                                              profile_names)

    return profiles_supported_artifact, profiles_supported_local


def set_text_of_supported_value(profile_value):
    """
    Set the text of the SUPPORTED value for the specified profile value

    :param profile_value: dictionary with the basic_network.py values of the specified profile
    :type profile_value: dict
    :return: the text for the SUPPORTED value of the profile e.g. YES, NO, INTRUSIVE
    :rtype: str
    """

    if profile_value.get('SUPPORTED') is True:
        text_for_supported_value = log.green_text('YES')
    elif profile_value.get('SUPPORTED') is not False:
        text_for_supported_value = log.yellow_text(profile_value.get('SUPPORTED'))
    else:
        text_for_supported_value = log.red_text('NO')

    return text_for_supported_value


def set_supported_value_text_and_get_profile_values_for_artifact_profile(artifact_profiles, profile):
    """
    Set the text for the nexus SUPPORTED value and get the profile values for the specified profile

    :param artifact_profiles: dictionary containing key,value pairs of attributes for profiles
    :type artifact_profiles: dict
    :param profile: profile to query
    :type profile: profile.Profile
    :return: tuple of strings
             nexus_version_supported, artifact_profile: text to display for SUPPORTED value of the nexus version,
              name of artifact profile
    :rtype: tuple
    """

    profile_name = getattr(profile, "NAME")
    nexus_version_supported = ''
    artifact_profile = artifact_profiles.get(profile_name)
    if artifact_profile:
        nexus_version_supported = set_text_of_supported_value(artifact_profile)
    else:
        log.logger.debug("Error getting profile from nexus version of {0}. May have been deprecated or "
                         "name changed.".format(profile_name))

    return nexus_version_supported, artifact_profile


def set_tabulated_info_for_local_version_supported(profile_value):
    """
    Set the text for the local version SUPPORTED value

    :param profile_value: dict of profile values in basic_network.py
    :type profile_value: dict
    :return: text to display for SUPPORTED value of the local version
    :rtype: str
    """

    local_version_supported = '-'
    if profile_value:
        local_version_supported = set_text_of_supported_value(profile_value)

    return local_version_supported


def get_text_value_for_cloud_supported(profile_value):
    """
    Return the text to display for the CLOUD_SUPPORTED value of the specified profile

    :param profile_value: dict of the profile values
    :type profile_value: dict
    :return: text to display
    :rtype: str
    """
    if profile_value.get('CLOUD_SUPPORTED') is False or profile_value.get('SUPPORTED') is False:
        cloud_supported_text_to_log = log.red_text('NO')
    elif profile_value.get('SUPPORTED') is not True:
        cloud_supported_text_to_log = log.yellow_text(profile_value.get('SUPPORTED'))
    else:
        cloud_supported_text_to_log = log.green_text('YES')
    return cloud_supported_text_to_log


def get_text_value_for_physical_supported(profile_value):
    """
    Return the text to display for the PHYSICAL_SUPPORTED value of the specified profile

    :param profile_value: dict of the profile values
    :type profile_value: dict
    :return: text to display
    :rtype: str
    """
    if profile_value.get('PHYSICAL_SUPPORTED') is False or profile_value.get('SUPPORTED') is False:
        physical_supported_text_to_log = log.red_text('NO')
    elif profile_value.get('SUPPORTED') is not True:
        physical_supported_text_to_log = log.yellow_text(profile_value.get('SUPPORTED'))
    else:
        physical_supported_text_to_log = log.green_text('YES')
    return physical_supported_text_to_log


def get_text_value_for_cloud_native_supported(profile_value):
    """
    Return the text to display for the CLOUD_NATIVE_SUPPORTED value of the specified profile

    :param profile_value: dict of the profile values
    :type profile_value: dict
    :return: text to display
    :rtype: str
    """
    cn_supported_value = profile_value.get('CLOUD_NATIVE_SUPPORTED')
    supported_value = profile_value.get('SUPPORTED')
    if supported_value is not True and supported_value is not False:
        cloud_native_supported_text_to_log = log.yellow_text(supported_value)
    elif not cn_supported_value or supported_value is False:
        cloud_native_supported_text_to_log = log.red_text('NO')
    else:
        cloud_native_supported_text_to_log = log.green_text('YES')
    return cloud_native_supported_text_to_log


def set_tabulated_info_profile_values(profile, running, local_version_supported,
                                      nexus_version_supported, profile_value, artifact_profile=None):
    """
    Set the tabulated info to display for local values when running the workload diff command
    :param profile: profile to log info for
    :type profile: enmutils_int.lib.profile.Profile
    :param running: whether the profile is running
    :type running: bool
    :param artifact_profile: dictionary containing key,value pairs of attributes for artifact profile
    :type artifact_profile: dict or None
    :param local_version_supported: text to display for the SUPPORTED value of the local version
    :type local_version_supported: str
    :param nexus_version_supported: text to display for the SUPPORTED value of the nexus version
    :type nexus_version_supported: str
    :param profile_value: dictionary containing key,value pairs of attributes for profile
    :type profile_value: dict
    :return: list of the text values to display
    :rtype: list
    """

    profile_name = getattr(profile, "NAME")
    if artifact_profile:
        priority = artifact_profile.get('PRIORITY') or '-'
        note = artifact_profile.get('NOTE') or '-'
    else:
        priority = profile_value.get('PRIORITY') or '-'
        note = profile_value.get('NOTE') or '-'

    profile_info = [log.cyan_text(profile_name),
                    log.green_text('YES') if running else log.red_text('NO'),
                    log.yellow_text(priority),
                    local_version_supported]

    if nexus_version_supported:
        profile_info.append(nexus_version_supported)
    profile_info.extend([get_text_value_for_physical_supported(profile_value),
                         get_text_value_for_cloud_supported(profile_value),
                         get_text_value_for_cloud_native_supported(profile_value), note])

    return profile_info


def set_tabulated_info(tabulate_data, profiles, profile_values_local, ignore, artifact_profiles=None, running=True):
    """
    Set the tabulated info to display when running the workload diff command

    :param tabulate_data: List of data
    :type tabulate_data: list
    :param profiles: list of profiles
    :type profiles: list
    :param profile_values_local: dict consisting of profile.NAME as key and dict of profile local values as values
    :type profile_values_local: dict
    :param ignore: List of profiles to ignore
    :type ignore: list
    :param artifact_profiles: dict consisting of profile.NAME as key and dict of profile values as values
    :type artifact_profiles: dict
    :param running: whether the profile is running
    :type running: bool
    :returns: List of table data
    :rtype: list
    """
    artifact_profile = None
    nexus_version_supported = None

    for profile in sorted(profiles, key=attrgetter('supported'), reverse=True):
        if profile.NAME in ignore:
            continue
        if artifact_profiles:
            nexus_version_supported, artifact_profile = (
                set_supported_value_text_and_get_profile_values_for_artifact_profile(
                    artifact_profiles, profile))

        profile_value = profile_values_local.get(profile.NAME)
        if not profile_value:
            log.logger.debug("Error getting profile in local version of {0}. May have been deprecated or name "
                             "changed.".format(profile.NAME))
        local_version_supported = set_tabulated_info_for_local_version_supported(profile_value)

        if profile_value:
            profile_info = set_tabulated_info_profile_values(profile, running,
                                                             local_version_supported, nexus_version_supported,
                                                             profile_value, artifact_profile)
        else:
            log.logger.debug("Error getting profile {0}. May have been deprecated or name "
                             "changed.".format(profile.NAME))
            continue

        tabulate_data.append(profile_info)
    return tabulate_data


def get_values_for_profile_from_python_dict(networks, network_key, profile_names):
    """
    Accesses and returns, the profile attributes to be set on the profile(s) with the start option

    :param networks: Dict of all network data
    :type networks: dict
    :param network_key: Type of network
    :type network_key: str
    :param profile_names: List of profile names
    :type profile_names: list
    :rtype: dict
    :returns: Dictionary containing key,value pairs of attributes for profiles
    """
    profiles_supported_flag_dict = {}
    # get size, platform, application

    if all([networks, network_key]):
        network = networks.get(network_key.lower())
        if network:
            for app in network.iteritems():
                profiles_supported_flag_dict = set_profiles_supported_flag(profiles_supported_flag_dict,
                                                                           profile_names, app)
        else:
            invalid_network_message = log.red_text('ERROR: Invalid network: {0}.\n'.format(network))
            config.set_prop(INVALID_VERSION_MESSAGE, invalid_network_message)
            log.logger.info(invalid_network_message)
    return profiles_supported_flag_dict


def set_profiles_supported_flag(profiles_supported_flag_dict, profile_names, app):
    """
    Set Profiles supported flag

    :param profiles_supported_flag_dict: Dictionary contain supported status for profiles
    :type profiles_supported_flag_dict: dict
    :param profile_names: List of profile names
    :type profile_names: list
    :param app: Dictionary of network values
    :type app: dict
    :return: Dictionary for items showing supported status for profiles
    :rtype: dict
    """
    if profile_names:
        for prof, v in app[1].items():
            if prof.upper() in profile_names:
                profiles_supported_flag_dict[prof] = {'SUPPORTED': v.get('SUPPORTED'),
                                                      'NOTE': v.get('NOTE'),
                                                      'PHYSICAL_SUPPORTED': v.get('PHYSICAL_SUPPORTED'),
                                                      'CLOUD_SUPPORTED': v.get('CLOUD_SUPPORTED'),
                                                      'CLOUD_NATIVE_SUPPORTED': v.get('CLOUD_NATIVE_SUPPORTED'),
                                                      'PRIORITY': v.get('PRIORITY')}
    else:
        for prof, v in app[1].items():
            profiles_supported_flag_dict[prof] = {'SUPPORTED': v.get('SUPPORTED'),
                                                  'NOTE': v.get('NOTE'),
                                                  'PHYSICAL_SUPPORTED': v.get('PHYSICAL_SUPPORTED'),
                                                  'CLOUD_SUPPORTED': v.get('CLOUD_SUPPORTED'),
                                                  'CLOUD_NATIVE_SUPPORTED': v.get('CLOUD_NATIVE_SUPPORTED'),
                                                  'PRIORITY': v.get('PRIORITY')}

    return profiles_supported_flag_dict


def get_all_profile_names():
    """
    Returns the profiles in the basic network

    :rtype: list
    :return: A sorted list of all profiles in the basic network
    """
    log.logger.debug("Getting profile names from the basic network")
    basic = get_all_networks().get('basic')
    profiles = []
    for app in basic.iterkeys():
        for profile in basic.get(app).iterkeys():
            profiles.append(profile.lower())
    log.logger.debug("Finished getting profile names from the basic network")
    return sorted(profiles)


def get_categories():
    """
    Gets all of the valid workload categories

    :rtype: set
    :returns: all valid categories:
    """
    return sorted(set([re.split(r'_\d{1,2}', profile)[0]
                       if re.search(r'\d+$', profile) and not re.search(r'setup', profile) else profile.split('_')[0]
                       for profile in get_all_profile_names()]))


def get_synced_count():
    """
    Return total nodes on the network and the total CM non-synchronised

    :return: Total nodes on the network and the total CM non-synchronised
    :rtype: tuple
    """
    user = get_workload_admin_user()
    status = CmManagement.get_status(user)
    un_synced = 0
    for value in status.itervalues():
        if "UNSYN" in value:
            un_synced += 1
    return un_synced, len(status)


def report_syncronised_level():
    """
    Function to determine the varying sync counts of the underlying network
    """
    un_synced, total = get_synced_count()
    if not un_synced <= (total * .40):
        log.logger.info(log.yellow_text("WARNING: Less than 60% of the network is synchronised.\n"
                                        "The number of cells managed mis-aligned with the actual number of cells in"
                                        " your network.\nConsequently there is a risk that the wrong profile load "
                                        "factor will be applied to your deployment."))


def get_difference_nodes_between_wlvm_and_enm():
    """
    Get and prints the difference nodes between the wlvm and ENM
    :return: Total nodes in workload pool and ENM, difference nodes between the workload pool and ENM.
    :rtype: list
    """
    enm_nodes_list = []
    display_enm_msg = True
    enm_message = ""
    wl_message = ""
    get_nodes_enm_url = "/managedObjects/query?searchQuery=select%20networkelement"
    user = enm_user_2.get_admin_user()
    response = user.get(get_nodes_enm_url)
    if response.ok:
        enm_nodes_list = list(set([str(node['mibRootName']) for node in response.json()]))
        nodes_count_in_enm = log.green_text("Total number of nodes in ENM: {0}".format(len(enm_nodes_list)))
    else:
        nodes_count_in_enm = log.red_text("\nUnable to get nodes data from ENM due to some error. Please try again....")
        display_enm_msg = False
    log.logger.info(nodes_count_in_enm)

    wl_nodes = node_pool_mgr.get_pool().wl_nodes
    wl_nodes_list = [str(node.node_id) for node in wl_nodes]
    nodes_count_in_wlpool = log.green_text("Total number of nodes in workload pool: {0}".format(len(wl_nodes_list)))
    log.logger.info(nodes_count_in_wlpool)

    for key in Counter(wl_nodes_list):
        if key in Counter(enm_nodes_list):
            wl_nodes_list.remove(key)
            enm_nodes_list.remove(key)

    if display_enm_msg:
        enm_message = (log.yellow_text("Total number of nodes that present in ENM but not in workload pool: ") +
                       log.red_text("{0} ".format(len(enm_nodes_list))) + log.cyan_text("{0}".format(enm_nodes_list)))

        wl_message = (log.yellow_text("\nTotal number of nodes that present in Workload pool "
                                      "but not in ENM: ") + log.red_text("{0} ".format(len(wl_nodes_list))) +
                      log.cyan_text("{0}".format(wl_nodes_list)))
    log.logger.info(enm_message)
    log.logger.info(wl_message)
    return [nodes_count_in_enm, nodes_count_in_wlpool, enm_message, wl_message]


def get_wl_poids():
    """
   Gets all the differnces between the ENM and WOrkloadPool Nodes wrt POIDS.
   """
    difference_nodes_poids = [['ENM NODE', 'POID', 'WORKLOAD POOL NODE', 'POID']]
    note_message = ""
    try:
        wl_poids_data = {node.node_id: node.poid for node in node_pool_mgr.get_pool().wl_nodes}
        enm_poids_data = deployment_info_helper_methods.build_poid_dict_from_enm_data()
        # poid data of nodes present only in workload pool
        wl_node_poids = [["", "", key, wl_poids_data.pop(key)] for key in
                         (list(set(wl_poids_data) - set(enm_poids_data)))]
        # poid data of nodes present only in ENM
        enm_node_poids = [[key, enm_poids_data.pop(key), "", "", ] for key in
                          (list(set(enm_poids_data) - set(wl_poids_data)))]
        # The difference of POID between the nodes present in both ENM and Workload Pool
        difference_nodes_poids.extend([list(wl + enm) for wl, enm in zip(sorted(wl_poids_data.items()),
                                                                         sorted(enm_poids_data.items()))
                                       if wl != enm])
        if wl_node_poids:
            difference_nodes_poids.extend(wl_node_poids)
        if enm_node_poids:
            difference_nodes_poids.extend(enm_node_poids)
        log.logger.debug("difference_nodes_poids: {0}".format(difference_nodes_poids))
        if len(difference_nodes_poids) > 1:
            poid_diff_message = (log.cyan_text("The differences of nodes poid data between the ENM and Workload Pool "
                                               "respectively.") + "\n" + tabulate(difference_nodes_poids,
                                                                                  headers="firstrow") + "\n" + " ")
        else:
            poid_diff_message = log.green_text("The nodes poid data is in sync between the Workload Pool and ENM.")
        note_message = log.yellow_text("\n" + "Note:\nYou need to restart the node-manager service in Workload VM "
                                              "manually using below command if Node POID data is not being updated "
                                              "in WL pool/ENM.\nCommand: 'service nodemanager restart'\n"
                                              "If there are nodes present on Workload Pool and not present on ENM "
                                              "either Remove/Add them from Workload Pool and vice versa.")
    except Exception:
        poid_diff_message = log.red_text("Unable to fetch POID data from Workload Pool/ENM.")
    log.logger.info(poid_diff_message)
    log.logger.info(note_message)
    return [poid_diff_message, note_message]
