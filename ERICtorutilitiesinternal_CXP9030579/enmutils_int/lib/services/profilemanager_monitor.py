# ********************************************************************
# Name    : Profile Manager Monitor
# Summary : This is the primary module to detect and rectify profiles which have gone to dead state or no longer active.
# ********************************************************************
import commands
import logging.handlers
import re
import sys
import time
from datetime import datetime

from enmutils.lib import process, timestamp, persistence

logger = logging.getLogger(__name__)
PROFILE_MONITOR_LOG_PATH = "/home/enmutils/services/profile_monitor.log"
BASE_LOG_DIRECTORY = "/var/log/enmutils/{0}"
PROFILE_LOG_DIRECTORY = BASE_LOG_DIRECTORY.format("daemon/{0}.log")
WORKLOAD_TOOL_PATH = "/opt/ericsson/enmutils/bin/workload"
WORKLOAD_OPS_LOG = BASE_LOG_DIRECTORY.format("workload_operations.log")

DEAD_PROFILES = []
EXCLUDED_PROFILES = ["CBRS_SETUP"]
TIMESTAMP_PATTERN = "%Y-%m-%d %H:%M:%S"


def init_logger():
    """
    Returns the logger for logging profile monitor information

    :raises RuntimeError: raised if logging fails to initialize

    :return: Returns the logger instance
    :rtype: `logging.Logger`
    """
    log_level = logging.DEBUG
    try:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler = logging.handlers.WatchedFileHandler(PROFILE_MONITOR_LOG_PATH)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(log_level)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        return logger
    except Exception as e:
        raise RuntimeError("Failed to initialise logging, error encountered :: {0}".format(str(e)))


def get_profile_process(profile_name):
    """
    Confirm the profile still has a process on the deployment.

    :param profile_name: Name of the profile to check for any existing process
    :type profile_name: str
    """
    global DEAD_PROFILES
    logger.debug("Querying deployment for process belonging to profile: {0}".format(profile_name))
    if not process.get_profile_daemon_pid(profile_name):
        DEAD_PROFILES.append(profile_name)
    logger.debug("Completed querying deployment for process belonging to profile: {0}".format(profile_name))


def get_no_longer_logging_profile(profile_name):
    """
    Get the total in minutes since the last log entry to the profile(s) log file

    :param profile_name: Profile name to be used to determine when it last created a log entry
    :type profile_name: str
    """
    last_log_entries = collect_log_entries(profile_name, "tail -20 {0}".format(
        PROFILE_LOG_DIRECTORY.format(profile_name.lower())), PROFILE_LOG_DIRECTORY.format(profile_name.lower()))
    logger.debug("Checking {0} log for time of last log entry.".format(profile_name))
    for log_entry in last_log_entries[::-1]:
        if re.match(r'^\d+-\d+-\d+', log_entry):
            datetime_str = log_entry.split(",")[0]
            logger.debug("Checking log entry: [{0}] if datetime object.".format(datetime_str))
            last_log_time = timestamp.convert_str_to_datetime_object(datetime_str, TIMESTAMP_PATTERN)
            if hasattr(last_log_time, 'now'):
                elapsed_time = datetime.now() - last_log_time
                if divmod(elapsed_time.total_seconds(), 60)[0] >= 300:
                    logger.debug("Profile has not logged in the past five hours, adding to DEAD profile list: "
                                 "[{0}].".format(profile_name))
                    global DEAD_PROFILES
                    DEAD_PROFILES.append(profile_name)
                break
    logger.debug("Completed checking {0} log for time of last log entry.".format(profile_name))


def collect_log_entries(profile_name, cmd, log_file):
    """
    Querying the supplied log file path, using the supplied command to retrieve entries for the supplied profile name.

    :param profile_name: Profile name to retrieve the log entries
    :type profile_name: str
    :param cmd: Command to use to retrieve the log entries
    :type cmd: str
    :param log_file: Path to the log file to query
    :type log_file: str

    :return: List containing log entries if found
    :rtype: list
    """
    logger.debug("Querying {0} for any entries containing profile: {1}.\tUsing command: [{2}]".format(
        log_file, profile_name, cmd))
    log_entries = []
    rc, output = commands.getstatusoutput(cmd)
    if not rc and output and 'Broken pipe' not in output and "write error" not in output:
        log_entries = output.split('\n')
    else:
        logger.debug("Unable to retrieve {0} entries for profile: [{1}], rc: [{2}], output: [{3}].".format(
            log_file, profile_name, rc, output))
    logger.debug("Completed querying {0} for any entries containing profile: {1}.".format(log_file, profile_name))
    return log_entries


def log_log_entries(profile_name):
    """
    Log the contents of the log file queries

    :param profile_name: Profile name to retrieve the log entries
    :type profile_name: str
    """
    logger.debug("###### Starting log collection for: [{0}] ######".format(profile_name))
    profile_log_path = PROFILE_LOG_DIRECTORY.format(profile_name.lower())
    logger.debug("")
    for line in collect_log_entries(profile_name, "tail -20 {0}".format(profile_log_path),
                                    profile_log_path):
        logger.debug(line)
    logger.debug("")
    for line in collect_log_entries(profile_name, "egrep -i {0} /var/log/messages".format(profile_name),
                                    '/var/log/message'):
        logger.debug(line)
    logger.debug("")
    for line in collect_log_entries(profile_name, 'tac {0} | egrep "Starting TEARDOWN" -m1 -B20'.format(
            profile_log_path), profile_log_path):
        logger.debug(line)
    logger.debug("###### Completed log collection for: [{0}] ######".format(profile_name))
    logger.debug("Querying redis for persisted exceptions for profile: [{0}]".format(profile_name))
    errors = persistence.get('{0}-errors'.format(profile_name))
    if errors:
        logger.debug(errors)
    logger.debug("Completed querying redis for persisted exceptions for profile: [{0}]".format(profile_name))


def update_list_of_no_longer_active_profiles(profile_name, profile):
    """
    Check if the supplied profile is DEAD, inactive or no longer logging

    :param profile_name: Name of the profile to check if still active on deployment
    :type profile_name: str
    :param profile: Profile object to check the state
    :type profile: `lib.profile.Profile`
    """
    if profile_name not in DEAD_PROFILES:
        get_profile_process(profile_name)
    if profile_name not in DEAD_PROFILES and profile.state not in ["SLEEPING"]:
        get_no_longer_logging_profile(profile_name)


def determine_last_related_log_entry(log_entries):
    """
    If there are multiple related log entries, select the most recent

    :param log_entries: List of log entries related to the profile
    :type log_entries: list

    :return: The most recent related log entry
    :rtype: str
    """
    relevant_log_entry = ""
    for index, log_entry in enumerate(log_entries):
        if index == 0:
            relevant_log_entry = log_entry
        else:
            if (timestamp.convert_str_to_datetime_object(log_entry.split(",")[0], TIMESTAMP_PATTERN) >
                    timestamp.convert_str_to_datetime_object(log_entries[index - 1].split(",")[0], TIMESTAMP_PATTERN)):
                relevant_log_entry = log_entry
    return relevant_log_entry


def get_expected_state_of_profile(profile_name):
    """
    Check the workload ops log for the last related ./workload command issued relating to the supplied profile

    :param profile_name: Name of the profile to check what action should be taken
    :type profile_name: str

    :return: The workload operation to trigger
    :rtype: str
    """
    logger.debug("Checking {0} for recent workload operations related to profile: [{1}]".format(
        WORKLOAD_OPS_LOG, profile_name))
    operations_mapping = {
        "restarting": "restart",
        "stopping": "stop",
        "starting": "restart"
    }
    now = datetime.now()
    time_str = "{0}-{1}-{2}".format(now.year, "{0}".format(now.month).zfill(2), "{0}".format(now.day).zfill(2))
    base_cmd = 'tac {0} | egrep -i {1} -m1 | egrep {2}'
    operation = "restarting"
    profile_app = re.split(r'_\d+', profile_name)[0]
    log_entries = []
    log_entries.extend(collect_log_entries(profile_name, base_cmd.format(WORKLOAD_OPS_LOG, "all", time_str),
                                           WORKLOAD_OPS_LOG))
    log_entries.extend(collect_log_entries(profile_name, base_cmd.format(WORKLOAD_OPS_LOG, profile_app, time_str),
                                           WORKLOAD_OPS_LOG))
    log_entries.extend(collect_log_entries(profile_name, base_cmd.format(WORKLOAD_OPS_LOG, profile_name, time_str),
                                           WORKLOAD_OPS_LOG))
    if log_entries:
        last_log_entry = determine_last_related_log_entry(log_entries)
        operation = last_log_entry.split(' ')[5].lower()
    logger.debug("Completed check of {0} for recent workload operations related to profile: [{1}]".format(
        WORKLOAD_OPS_LOG, profile_name))
    return operations_mapping.get(operation)


def profile_clean_up(profile):
    """
    Attempt to clean up the profile processes and manually trigger the teardown without cleaning up persistence
    :param profile: Profile object to teardown
    :type profile: `lib.profile.Profile`
    """
    logger.debug("Performing profile cleanup on {0}".format(profile.NAME))
    try:
        process.kill_spawned_process(profile.NAME, profile.pid)
    except Exception as e:
        logger.debug(str(e))
    finally:
        logger.debug("Invoking profile {0} teardown".format(profile.NAME))
        profile.teardown()
    logger.debug("Cleanup actions complete")


def trigger_profile_operation(profile_name, profile, operation):
    """
    Perform the supplied ./workload operation on the supplied profile

    :param profile_name: Name of the profile to supply to workload tool
    :type profile_name: str
    :param operation: Workload operation to be called
    :type operation: str
    :param profile: Profile object to clean up
    :type profile: `lib.profile.Profile`
    """
    logger.debug("Attempting to {1} workload profile: [{0}]".format(profile_name, operation))
    profile_clean_up(profile)
    if operation == 'stop':
        logger.debug("Completed workload stop operation, profile: [{0}].".format(profile_name))
        return
    cmd = '{0} restart -xN {1} --force-stop --message="automatic {1} triggered due to unwanted profile state."'.format(
        WORKLOAD_TOOL_PATH, profile_name)
    rc, output = commands.getstatusoutput(cmd)
    if rc and "unsupported" not in output:
        logger.debug("Unable to restart profile, rc: [{0}], output: [{1}].".format(rc, output))
    else:
        logger.debug("Completed workload restart profile: [{0}]".format(profile_name))


def confirm_profile_state(profile_name, profile, operation):
    """
    Check if the profile has changed to an expected state from the previous workload command

    :param profile_name: Name of the profile to be checked
    :type profile_name: str
    :param operation: Workload operation which we tried to perform
    :type operation: str
    :param profile: Profile object to clean up
    :type profile: `lib.profile.Profile`
    """
    states = {"restart": ["RESTARTING", "STARTING", "STOPPING", "COMPLETED"], "stop": ["STOPPING"]}
    logger.debug("Confirming profile: [{0}] is one of {1}".format(profile_name, states.get(operation)))
    if getattr(profile, 'state', None) not in states.get(operation) or getattr(profile, 'status', None) == "DEAD":
        if operation in ['start', 'restart']:
            trigger_profile_operation(profile_name, profile, operation)
        else:
            profile_clean_up(profile)


def verify_profile_state(profile_list):
    """
    Verify if supplied profile(s) are in unwanted state

    :param profile_list: List of profile(s) to verify are still active
    :type profile_list: list

    :returns: List of profile names identified as DEAD or inactive |
    :rtype: list
    """
    if not logger.handlers:
        init_logger()
    inactive_profiles = []
    global DEAD_PROFILES
    DEAD_PROFILES = [profile.NAME for profile in profile_list if profile.status == "DEAD"]
    logger.debug("Profiles status returning as 'DEAD':: [{0}]".format(DEAD_PROFILES))
    active_profiles = [profile for profile in profile_list if profile.state != "COMPLETED"]
    for profile in active_profiles:
        profile_name = getattr(profile, 'NAME')
        if check_if_profile_has_completed(profile_name):
            logger.debug("Profile {0} has gone to COMPLETED state or has been removed since last check "
                         "and therefore no longer regarded as being active - skipping".format(profile_name))
            continue
        if profile_name not in DEAD_PROFILES and profile_name not in EXCLUDED_PROFILES:
            update_list_of_no_longer_active_profiles(profile_name, profile)
        if profile_name in DEAD_PROFILES:
            inactive_profiles.append(profile_name)
            log_log_entries(profile_name)
            operation = get_expected_state_of_profile(profile_name)
            trigger_profile_operation(profile_name, profile, operation)
            sleep_time = 300  # Based upon the time set in profile_manager:checks_profile_is_stopping
            logger.debug("Sleeping for {0} seconds before checking updated state of profile.".format(sleep_time))
            time.sleep(sleep_time)
            confirm_profile_state(profile_name, profile, operation)
    logger.debug("Completed verification checks, returning {0} inactive profiles.".format(len(inactive_profiles)))
    return inactive_profiles


def check_if_profile_has_completed(profile_name):
    """
    Check if profile has gone to COMPLETED
    :param profile_name: Profile Name
    :type profile_name: str
    :return: Boolean to indicate that profile is in expected state
    :rtype: bool
    """
    logger.debug("Checking current status of profile {0}".format(profile_name))
    profile = persistence.get(profile_name)
    if profile:
        state, status = getattr(profile, "state"), getattr(profile, "status")
        logger.debug("Profile {0} status is now: {1}-{2}".format(profile_name, state, status))
        return True if state == "COMPLETED" and status in ["OK", "WARNING", "ERROR"] else False
    else:
        logger.debug("Profile key not found in persistence - profile no longer running")
        return True
