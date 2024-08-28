# ********************************************************************
# Name    : Load Manager
# Summary : Functional module primarily used by workload ops. Allows
#           for querying of the workload REDIS objects, get active
#           profiles, get profile(s) objects, perform the exclusive
#           profile allocation.
# ********************************************************************

import datetime
import pkgutil
import re
import time
import xml.etree.ElementTree

import unipath
from packaging import version

from enmutils.lib import log, persistence, mutexer, process
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib import node_pool_mgr, profile
from enmutils_int.lib.common_utils import (get_installed_version, filter_artifact_dict_for_profile_keys,
                                           return_dict_from_json_artifact)
from enmutils_int.lib.nexus import check_nexus_version, download_mavendata_from_nexus
from enmutils_int.lib.nrm_default_configurations import profile_values, basic_network
from enmutils_int.lib.services import nodemanager_adaptor
from enmutils_int.lib.workload_network_manager import InputData
from enmutils_int.lib.node_pool_mgr import ProfilePool

WORKLOAD_PATH = unipath.Path(pkgutil.get_loader('enmutils_int').filename).child("lib").child("workload")
INT_PACKAGE = "ERICtorutilitiesinternal_CXP9030579"
IGNORE_PROFILES = []


def is_profile_in_state(profile_name, state="RUNNING"):

    profile_dict = get_persisted_profiles_by_name([profile_name])
    if profile_dict and (profile_dict[profile_name].state == state):
        return True

    return False


def clear_profile_errors(profile_names=None):
    """
    Clears error information for profiles

    :param profile_names: list of specific profiles names to clear (list)
    :type profile_names: list
    """
    profiles = profile_names or get_active_profile_names()
    for profile in profiles:
        persistence.remove("%s-errors" % profile.upper())
        persistence.remove("%s-warnings" % profile.upper())
        log.logger.info("Successfuly removed errors and warnings for profile: {}".format(profile))


def get_start_time_of_profile(profile_name):
    """
    Returns the start_time of a profile given its name

    :param profile_name: the name of the profile (str)
    :type profile_name: str
    :returns: start time of profile (str)
    :rtype: str
    """
    profile_key = profile_name.upper()
    if not persistence.has_key(profile_key):
        log.logger.debug("{0} profile is not running on this deployment".format(profile_key))
        return

    else:
        profile = persistence.get(profile_key)
        return profile.start_time


def wait_for_setup_profile(profile_name, state_to_wait_for="RUNNING", status=None, timeout_mins=20, sleep_between=5,
                           wait_for_flag=False, flag=None):  # NOSONAR
    """
    Blocks code flow of control until the specified profile has finished starting

    :param profile_name: indicates which setup profile we are waiting to complete (str)
    :type profile_name: str
    :param state_to_wait_for: the state which is queried.
    :type state_to_wait_for: str
    :param status: status of a set up profile - ERROR, OK, DEAD
    :type status: str
    :param sleep_between: sleep time between query for profile status
    :type sleep_between: int
    :param timeout_mins: timeout of this function in minutes
    :type timeout_mins: int
    :param wait_for_flag: argument to indicate that profiles should look for a flag instead of completion status
    :type wait_for_flag: bool
    :param flag: flag to wait for
    :type flag: str

    :return: returns None
    :rtype: None

    :raises EnvironError : if status of set up profile is not equal to expected status
    """

    profile_key = profile_name.upper()
    msg = ("Status of {0} profile is '{1}'. Expected status: '{2}'. Current profile will start only if {0} is {3} with "
           "{2} status. Please refer {0} profile logs for more")
    if not persistence.has_key(profile_key):
        log.logger.debug("{0} profile is not running on this deployment".format(profile_key))
        return

    timeout = (datetime.datetime.now() + datetime.timedelta(minutes=timeout_mins))

    while datetime.datetime.now() < timeout:
        if not persistence.has_key(profile_key):
            log.logger.debug("{0} profile is no longer running on this deployment".format(profile_key))
            return
        profile = persistence.get(profile_key)
        if not wait_for_flag:
            if (profile.state != "STARTING" and (profile.state == state_to_wait_for or profile.state == "COMPLETED")) or profile.status == "DEAD":
                return verify_profile_status(profile, profile_name, status, state_to_wait_for, msg)

        elif flag and hasattr(profile, "FLAG") and profile.FLAG == flag:
            return
        log.logger.info(log.red_text("Profile: {0} is not yet {1} waiting for {2} seconds".format(profile_name, state_to_wait_for, sleep_between)))
        time.sleep(sleep_between)
    log.logger.debug("{0} failed to move to state {1} within the timeout period ({2} minutes)"
                     "".format(profile_key, state_to_wait_for, timeout_mins))


def verify_profile_status(profile_obj, profile_name, status, state_to_wait_for, msg):
    """
    Verifies profile status with expected status and raises EnvironError, if status of set up profile is
    not equal to expected status.

    :param profile_name: indicates which setup profile we are waiting to complete
    :type profile_name: str
    :param status: status of a setup profile - ERROR, OK, DEAD
    :type status: str
    :param profile_obj: Profile object
    :type profile_obj: `enmutils_int.lib.profile.Profile`
    :param state_to_wait_for: the state which is queried.
    :type state_to_wait_for: str
    :param msg: profile error message
    :type msg: str

    :raises EnvironError : if status of set up profile is not equal to expected status
    """
    if status and profile_obj.status == status:
        return
    elif status and profile_obj.status != status:
        raise EnvironError(msg.format(profile_name, profile_obj.status, status, state_to_wait_for))
    else:
        return


def get_active_profile_names():
    """
    B{Gets a set of profile names active on the system}

    :rtype: set
    :return: Set of the active profiles on the system
    """

    return persistence.get("active_workload_profiles") or set()


def _get_profile(name):
    """
    Gets the singleton profile instance

    :type name: string
    :param name: name of the profile instance we want to return

    :return: the singleton object for the specified profile
    :rtype: object
    """
    module = __import__('enmutils_int.lib.workload.{0}'.format(name.lower()), fromlist=[''])
    return getattr(module, name.lower())


def get_all_active_profiles(active_profiles=None, diff=False):
    """
    Gets the active profiles on the system
    :param active_profiles: List of profile names to retrieve from persistence
    :type active_profiles: list
    :param diff: Boolean to retrieve existing diff persisted objects
    :type diff: bool
    :rtype: dict
    :return: Dictionary of active profiles {PROFILE_NAME: PROFILE_OBJECT}
    """
    log.logger.debug("Getting all active profiles")
    return get_persisted_profiles_by_name(active_profiles, diff)


def get_persisted_profiles_by_name(profile_names=None, diff=False):
    """
    Gets the active profiles on the system
    :param profile_names: List of profile names to retrieve from persistence
    :type profile_names: list
    :param diff: Boolean to retrieve existing diff persisted objects
    :type diff: bool
    :return: Dictionary of active profiles {PROFILE_NAME: PROFILE_OBJECT}
    :rtype: dict
    """
    log.logger.debug("Getting the active profile objects from persistence")
    all_active_profiles = {}
    if not profile_names:
        profile_names = get_active_profile_names()

    if profile_names:
        profile_names = [p.upper() for p in profile_names]
        if diff:
            persisted_profiles = get_existing_diff_objects(profile_names)
        else:
            persisted_profiles = persistence.get_keys(profile_names)

        for profile_name in profile_names:
            for profile_obj in persisted_profiles:
                if hasattr(profile_obj, "NAME") and profile_name == profile_obj.NAME:
                    all_active_profiles[profile_name] = profile_obj

    log.logger.debug("Number of Active profile objects: {0}".format(len(all_active_profiles)))
    return all_active_profiles


def get_existing_diff_objects(profile_names):
    """
    Gets existing diff objects and profile objects if diff object does not exist for a profile
    :param profile_names: List of profile names to retrieve from persistence
    :type profile_names: list
    :return: List of persisted profile objects (existing diff profile objects and profile objects)
    :rtype: list
    """
    log.logger.debug("Getting existing diff profile objects")
    diff_names = ["{0}-diff".format(profile_name.upper()) for profile_name in profile_names]
    persisted_diff_profiles = persistence.get_keys(diff_names)
    copy_profile_names = profile_names[:]
    if persisted_diff_profiles:
        for diff_profile in persisted_diff_profiles:
            if any(diff_profile.NAME in profile_name for profile_name in copy_profile_names):
                copy_profile_names.remove(diff_profile.NAME)
    persisted_full_profiles = persistence.get_keys(copy_profile_names)
    persisted_profiles = persisted_diff_profiles + persisted_full_profiles
    log.logger.debug("Number of diff objects: [{0}] Number of normal profile objects: [{1}]".format(
        len(persisted_diff_profiles), len(persisted_full_profiles)))
    return persisted_profiles


def kill_profile_daemon_process(profile_name):
    """
    Kills a profile if a process is running. Use if profile not in persistence.
    Will also kill forked (child) processes which will have the same name and arguments but different pid to parent

    :param profile_name: Profile name
    :type profile_name: str
    """

    for pid in process.get_profile_daemon_pid(profile_name):
        process.kill_process_id(int(pid))


def get_dependent_profiles(profiles):
    """
    Returns a set of dependent profiles

    :param profiles: list of profile names
    :type profiles: list
    :return: dependent_profiles: set, set of profile names of profiles that are dependent on other profiles
    :rtype: set
    """
    basic = 'basic'
    dependent_profiles_dict, dependent_profiles = {}, []
    for key in profile_values.networks.get(basic).iterkeys():
        for profile in profile_values.networks.get(basic).get(key):
            if profile_values.networks.get(basic).get(key).get(profile).get(basic_network.DEPENDENT, []):
                dependent_profiles_dict[profile] = profile_values.networks.get(basic).get(key).get(profile).get(basic_network.DEPENDENT)
    log.logger.debug("Dependency dictionary - {0}".format(dependent_profiles_dict.items()))
    for profile in profiles:
        if profile in dependent_profiles_dict:
            dependent_profiles.extend(dependent_profiles_dict.get(profile))
    log.logger.debug("Dependent profiles are - {0}".format(set(dependent_profiles)))
    return set(dependent_profiles)


def get_profiles_with_priority(priority, profiles):
    """
    Returns a set of profiles that contain the specified priority rating

    :param priority: str, specified priority rating
    :type priority: str
    :param profiles: list, list of profile names
    :type profiles: list
    :return: profiles_with_priority: set, set of profile names of profiles that have the specified priority rating
    :rtype: set
    :raises RuntimeError: raises if priority is not a digit
    """
    if not priority.isdigit():
        raise RuntimeError("Invalid priority provided: {0}".format(priority))
    profiles_with_priority = []
    basic = 'basic'
    for key in profile_values.networks.get(basic).iterkeys():
        for profile in profile_values.networks.get(basic).get(key):
            if profile_values.networks.get(basic).get(key).get(profile).get(basic_network.PRIORITY) is not None:
                if (profile_values.networks.get(basic).get(key).get(profile).get(basic_network.PRIORITY) ==
                        int(priority)):
                    profiles_with_priority.append(profile)
    return set(profiles).intersection(profiles_with_priority)


def get_persisted_profiles_status_by_name(priority, profile_names=None):
    """
    Gets the active profiles status on the system

    :type priority: str
    :param priority: priority rating specified

    :type profile_names: list
    :param profile_names: list of profile names to retrieve from persistence

    :rtype: list
    :return: list of dictionary(ies) of active profiles status'
    """
    log.logger.debug("Get the active profiles status - started")
    active_profile_names = get_active_profile_names()

    if profile_names:
        profiles = [p.upper() for p in profile_names]
    else:
        profiles = get_all_profile_names_from_persistence()
    profiles_missing_from_active_profile_names = [profile_name for profile_name in profiles
                                                  if profile_name not in active_profile_names and profile_name in
                                                  get_all_active_profiles(profiles).keys()]
    if profiles_missing_from_active_profile_names:
        log.logger.debug("Profiles not listed in active_workload_profiles key in persistence: {0} - updating now"
                         .format(profiles_missing_from_active_profile_names))
        with mutexer.mutex("workload_profile_list", persisted=True):
            active_profile_names.update(profiles_missing_from_active_profile_names)
            persistence.set("active_workload_profiles", active_profile_names, -1)

    if priority:
        profiles = get_profiles_with_priority(priority, profiles)

    profile_keys = ["{0}-status".format(profile.upper()) for profile in profiles]

    profile_status_objects = persistence.get_keys(profile_keys)
    log.logger.debug("Get the active profiles status - complete")
    return profile_status_objects


def get_all_profile_names_from_persistence():
    """
    Get all profile names from persistence based on the existence of 2 profile-related keys whose names have
    the following format:
        1. <profile_name>
        2. <profile_name>-status

    :return: List of profile names
    :rtype: list
    """
    list_of_all_keys_in_persistence = persistence.get_all_keys()
    status_keys = [key_name.replace("-status", "") for key_name in list_of_all_keys_in_persistence
                   if "-status" in key_name]
    return [key_name for key_name in status_keys if key_name in list_of_all_keys_in_persistence]


def get_profile_objects_from_profile_names(profile_names):
    """
    Get profile objects for supplied list of profile names

    :param profile_names: list of profile names
    :type profile_names: list

    :rtype: list of profile.Profile objects
    :returns: list of
    """
    return [_get_profile(prof) for prof in profile_names]


def get_profile_update_version(profile, json_dict=None):
    """
    Get the update version for the provided profile from the json_dict provided

    :type profile: str
    :param profile: Name of the profile
    :type json_dict: dict
    :param json_dict: Dictionary generated from json artifact downloaded from nexus

    :rtype: int
    :return: Integer value for the profiles update version
    """
    app = re.split(r'_[0-9]', profile.lower())[0].replace('_setup', '')
    if not json_dict:
        json_dict = return_dict_from_json_artifact(get_installed_version(INT_PACKAGE))
    try:
        return json_dict.get('basic').get(app).get(profile.upper()).get('UPDATE_VERSION')
    except (AttributeError, KeyError) as e:
        log.logger.debug("Failed to retrieve {0} from artifact, response: {1}".format(profile.upper(), e.message))
        # Most likely in this situation, it is a new profile and rather than raise an exception
        # return a stupidly high update version and do nothing
        return 99999


def detect_and_create_renamed_objects(updated_profiles):
    """
    Check for renamed profile(s) and update the updated list if found

    :param updated_profiles: List of the profile objects which have been updated
    :type updated_profiles: list

    :return: List of updated profiles objects
    :rtype: list
    """
    log.logger.debug("Checking for renamed profiles")
    for updated_profile in updated_profiles:
        if updated_profile.NAME in basic_network.RENAMED_PROFILES.keys():
            renamed_profile = basic_network.RENAMED_PROFILES.get(updated_profile.NAME)
            log.logger.debug("Renamed profile [{0}] added to updated list.".format(renamed_profile))
            updated_profiles.append(RenamedProfile(name=renamed_profile))
    return updated_profiles


def get_updated_active_profiles():
    """
    Get all active profiles objects, that were updated on the latest installed rpm

    :return: List of updated profiles objects
    :rtype: list
    """
    update_file_ver = None
    profiles = []
    installed_ver = get_installed_version("ERICtorutilitiesinternal_CXP9030579")

    for profile in get_persisted_profiles_by_name(diff=True).values():
        # get version and update_version from an active profile (redis)
        profile_ver_running = getattr(profile, "version", None)
        update_ver_running = getattr(profile, "update_version", 0)
        # get version and update_version of a profile - based on a profile .py file
        try:
            update_file_ver = get_profile_update_version(profile.NAME)
        except EnvironError as e:
            log.logger.debug(e.message)
        if not update_file_ver:
            profile_object_from_file = get_profile_objects_from_profile_names([profile.NAME])[0]
            update_file_ver = getattr(profile_object_from_file, "UPDATE_VERSION", 0)
        if version.parse(profile_ver_running) < version.parse(installed_ver) and update_ver_running < update_file_ver:
            profiles.append(profile)
            log.logger.debug('Profile: {0} was updated on currently installed rpm: {1}, profile_ver_running: {2}, '
                             'update_ver_running: {3}, update_file_ver: {4}'.format(profile, installed_ver,
                                                                                    profile_ver_running,
                                                                                    update_ver_running,
                                                                                    update_file_ver))

    profiles = detect_and_create_renamed_objects(profiles)

    return profiles


def get_active_foundation_profiles():
    """
    Returns active foundation profiles.
    :return: profile_obj that has FOUNDATION
    :rtype: object
    """
    return [profile for profile, profile_obj in get_persisted_profiles_by_name().iteritems()
            if hasattr(profile_obj, "FOUNDATION") and profile_obj.FOUNDATION]


def wait_for_stopping_profiles(profile_dict, wait_time=60 * 60 * 3, force_stop=False, jenkins=False,
                               interim_time=30, time_interval=10):
    """
    Function to wait for profiles to stop running.
    :param profile_dict: profile dict {profile_name: profile_object}
    :type profile_dict: dict
    :param wait_time:  time in seconds to wait for profiles to stop
    :type wait_time: int
    :param force_stop: if foundation profiles are to be stopped.
    :type force_stop: bool
    :param jenkins: Boolean indicating the operation is an automated one, and the loggging should be output to console
    :type jenkins: bool
    :param interim_time: Time in seconds to wait between logging to the debug log
    :type interim_time: int
    :param time_interval: Time in seconds to wait between checks
    :type time_interval: int

    :raises Exception: raised if the Restart exceeds the 3 hour limitation and the jenkins flag is set
    """
    time_slept = 0
    stopping_profiles = _get_stopping_profiles(profile_dict, force_stop=force_stop)
    if stopping_profiles:
        log.logger.info(log.green_text("Waiting for profile(s) to stop: "
                                       "{0}".format(",".join(stopping_profiles.keys()))))
    while stopping_profiles and time_slept < wait_time:
        time.sleep(time_interval)
        time_slept += time_interval
        if time_slept % interim_time == 0:
            message = "The following profiles are still stopping: {}".format(stopping_profiles.keys())
            log.logger.debug(message)
            if jenkins:
                log.logger.info(message)
        stopping_profiles = _get_stopping_profiles(profile_dict, force_stop=force_stop)

    if jenkins and stopping_profiles:
        raise Exception("Profile stop has timed out.")


def _get_stopping_profiles(profile_dict, force_stop=False):
    """
    Returns profiles which are still stopping.
    :param profile_dict: profile dict {profile_name: profile_object}
    :type profile_dict: dict
    :param force_stop: if foundation profiles are to be stopped.
    :type force_stop: bool
    :return: profiles that are stopping
    :rtype: dict
    """
    foundation = []
    if not force_stop:
        foundation = get_active_foundation_profiles()

    stopping_profiles = get_persisted_profiles_by_name([profile for profile in profile_dict.keys()]).keys()

    return {profile: profile_obj for profile, profile_obj in profile_dict.iteritems() if
            profile in stopping_profiles and profile not in foundation}


def allocate_exclusive_nodes(exclude=None, service_to_be_used=False):
    """
    Method to allocate exclusive nodes before starting profiles

    :type exclude: list
    :param exclude: List of `profile.Profile` objects to exclude
    :type service_to_be_used: bool
    :param service_to_be_used: Boolean to indicate if service is to be used to allocate nodes

    :return: true if required nodes are met requirements
    :rtype: bool
    """
    log.logger.debug("Determine list of exclusive profiles")
    profiles = _retrieve_all_exclusive_profiles(exclude=exclude)
    if not profiles:
        return False
    log.logger.warn("Currently performing allocation actions, please wait.")

    log.logger.debug("Processing the following profiles '{0}'".format([item.NAME for item in profiles]))
    for profile_obj in profiles:
        log.logger.debug("Allocating nodes to {0} if not already allocated".format(profile_obj.NAME))
        if not check_if_required_allocated_node_count_reached([profile_obj]):
            try:
                log.logger.debug("Allocate Nodes to profile {0}".format(profile_obj.NAME))
                if service_to_be_used:
                    nodemanager_adaptor.allocate_nodes(profile_obj)
                else:
                    node_pool_mgr.get_pool().allocate_nodes(profile_obj)
            except Exception as e:
                log.logger.debug("Failed to correctly allocate nodes, response: {0}".format(str(e)))

    log.logger.debug("Check if all profiles reached their target node count")
    result = check_if_required_allocated_node_count_reached(profiles)

    log.logger.debug("Allocate nodes to exclusive profiles result: {0}".format(result))

    return result


def check_if_required_allocated_node_count_reached(profiles_to_check):
    """
    Check if required allocated node count has been reached

    :param profiles_to_check: List of Profile objects
    :type profiles_to_check: list
    :return: Boolean to indicate if required number of nodes has been allocated
    :rtype: bool
    """
    log.logger.debug("Checking if required allocated node count has been reached for '{0}'"
                     .format([item.NAME for item in profiles_to_check]))
    result = True
    for profile_obj in profiles_to_check:
        log.logger.debug("Processing profile {0}".format(profile_obj.NAME))
        allocated = (len([node for node in node_pool_mgr.cached_nodes_list if profile_obj.NAME in node.profiles]))
        log.logger.debug("Number of nodes already allocated: {0}".format(allocated))
        if hasattr(profile_obj, 'TOTAL_NODES'):
            log.logger.debug("Profile has TOTAL_NODES attribute: {0}".format(profile_obj.TOTAL_NODES))
            result = bool(result and bool(allocated == profile_obj.TOTAL_NODES))
        elif hasattr(profile_obj, 'NUM_NODES'):
            log.logger.debug("Profile has NUM_NODES attribute: {0}".format(profile_obj.NUM_NODES))
            result = bool(result and allocated == sum(profile_obj.NUM_NODES.values()))
        log.logger.debug("Required allocated count has been reached: {0}".format(result))

    if len(profiles_to_check) > 1:
        log.logger.debug("Overall result: {0}".format(result))

    return result


def deallocate_all_exclusive_nodes(active, stop_all=False, service_to_be_used=False):
    """
    Deallocate nodes from all exclusive profiles, if they are not started

    :type active: list
    :param active: List of `profile.Profile` objects (if any are active)
    :type stop_all: bool
    :param stop_all: Boolean to indicate if stop all called
    :type service_to_be_used: bool
    :param service_to_be_used: Boolean to indicate if service to be used
    """
    node_mgr = node_pool_mgr if not service_to_be_used else nodemanager_adaptor

    currently_active = get_all_active_profiles()
    # If Ap 01 is running but stop all is called, allow Ap to handle its own deallocation of nodes
    if currently_active and 'AP_01' in currently_active and 'AP_01' not in active:
        active.append('AP_01')
    if not stop_all:
        active += currently_active
    profiles = _retrieve_all_exclusive_profiles(active)
    for prof in profiles:
        if ProfilePool().allocated_nodes(prof):
            node_mgr.deallocate_nodes(prof)
            log.logger.info(log.cyan_text("Nodes were released from the inactive exclusive profile: {0}".format(prof)))
        else:
            log.logger.info(log.cyan_text("The profile: '{0}' is not allocated to any node".format(prof)))


def _retrieve_all_exclusive_profiles(exclude=None):
    """
    Checks the current network profiles(and default if not current) for exclusive profiles

    :type exclude: list
    :param exclude: List of `profile.Profile` objects to exclude

    :rtype: list
    :return: List of EXCLUSIVE profile objects names that are exclusive
    """
    log.logger.debug("Retrieve list of Exclusive profiles started")
    data = InputData()
    exclude = exclude or []
    exclusive_profiles = set(data.get_all_exclusive_profiles)
    profiles = []
    for prof in [exc_profile for exc_profile in exclusive_profiles if exc_profile not in set(exclude)]:
        temp_profile = profile.ExclusiveProfile(prof)
        profile_values = data.get_profiles_values(prof.split('_')[0], prof)
        for k, v in profile_values.iteritems():
            setattr(temp_profile, k, v)
        profiles.append(temp_profile)

    list_of_profiles = list(reversed(sorted(profiles, key=lambda x: profiles[0].NAME != 'CMIMPORT_02')))
    log.logger.debug("Retrieved list of {0} Exclusive profiles".format(len(list_of_profiles)))
    return list_of_profiles


def get_new_profiles(previous_rpm=None):
    """
    Return the profile created between the currently installed rpm, and the specified or last rpm built

    :type previous_rpm: str
    :param previous_rpm: Version number of the rpm to used for comparison

    :rtype: list
    :return: List of the profile names
    """
    installed_version, previous_version = get_comparative_versions()
    if previous_rpm:
        previous_version = previous_rpm
    installed_profiles = filter_artifact_dict_for_profile_keys(installed_version)
    previous_profiles = filter_artifact_dict_for_profile_keys(previous_version)
    new_profiles = installed_profiles.difference(previous_profiles)

    return [str(_) for _ in new_profiles]


def get_updated_profiles(previous_rpm=None):
    """
    Get all profiles objects, that were updated on the latest installed rpm

    :type previous_rpm: str
    :param previous_rpm: Version number of the rpm to used for comparison

    :rtype: list
    :return: List of the profile names
    """
    installed_version, previous_version = get_comparative_versions()
    if previous_rpm:
        previous_version = previous_rpm
    installed_profiles = filter_artifact_dict_for_profile_keys(installed_version)
    installed_dict = return_dict_from_json_artifact(installed_version)
    previous_dict = return_dict_from_json_artifact(previous_version)
    updated_profiles = []
    for profile in installed_profiles:
        if get_profile_update_version(profile, installed_dict) > get_profile_update_version(profile, previous_dict):
            updated_profiles.append(profile)
    return updated_profiles


def get_comparative_versions():
    """
    Returns the currently installed version of the rpm, and the previous version

    :rtype: str
    :return: Str versions of installed and previous (or best guess) rpm
    :raises EnvironError: raises if there is Unknown in installed version
    """
    log.logger.debug("Determining installed and previous versions of the internal rpm")
    installed_version = get_installed_version(INT_PACKAGE)
    if 'Unknown' in installed_version:
        raise EnvironError("Failed to determine installed rpm version.")

    local_file_path = download_mavendata_from_nexus()

    if local_file_path:
        xml_root = xml.etree.ElementTree.parse(local_file_path).getroot()
        all_rpm_versions = [_.text for _ in xml_root.iter("version")]
        previous_version = get_previous_version(installed_version, all_rpm_versions)
    else:
        raise EnvironError("Unexpected error - xml not downloaded from nexus")

    log.logger.debug("Installed rpm version: {0} Previous rpm Version: {1}".format(installed_version, previous_version))
    return installed_version, previous_version


def get_previous_version(installed_version, all_rpm_versions):
    """
    Returns a previous version of the rpm that is found on both internal and production packages

    :type installed_version: str
    :param installed_version: Current version of the installed rpm
    :type all_rpm_versions: list
    :param all_rpm_versions: List of all rpms from nexus to compare

    :rtype: str
    :return: Str versions of previous (or best guess) rpm
    :raises EnvironError: raises if there is no previous rpm found
    """
    for index, version in enumerate(all_rpm_versions):
        if installed_version == version:
            while index != 0:
                previous_version = all_rpm_versions[index - 1]
                if previous_version and check_nexus_version("int", previous_version):
                    log.logger.debug("Found installed version: {0} on nexus and internal rpm".format(previous_version))
                    return previous_version
                index -= 1
            raise EnvironError("Unexpected error - unable to determine/verify previous rpm version")


class RenamedProfile(object):

    def __init__(self, name):
        """
        Init method

        :param name: Name of the profile
        :type name: str
        """
        self.NAME = name
