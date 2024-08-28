# ********************************************************************
# Name    : Common Utilities
# Summary : Contains commonly used functionality, user creation and
#           deletion, collection manipulation, process management,
#           and other ad-hoc functionality.
# ********************************************************************

import os
import pkgutil
import random
import re
import signal
import time
from collections import OrderedDict
from datetime import date

import unipath
from enmutils.lib import log, shell, filesystem, persistence, mutexer, process
from enmutils.lib.exceptions import EnvironError, NetsimError, ScriptEngineResponseValidationError, EnmApplicationError
from enmutils_int.lib.netsim_executor import check_nodes_started
from enmutils_int.lib.netsim_operations import PowerNodes
from enmutils_int.lib.enm_user import get_workload_admin_user, User
from enmutils_int.lib.nexus import download_artifact_from_nexus
from enmutils_int.lib.py_json_html_converter import get_json_from_a_file, convert_from_json_to_dict

STORAGE_DIR = "/home/enmutils"
installed_versions = {}
EXCLUDED_PROFILES = ["GEO_R_01"]


def merge_dict(base_dict, built_dict):
    """
    Merges the built up dictionary to the base dictionary containing all the sorted information

    :type base_dict: dict
    :param base_dict: The base dictionary which you want to merge into
    :type built_dict: dict
    :param built_dict: A dictionary containing information you've gathered which is to be merged to base
    """

    for key, value in built_dict.items():
        if key in base_dict.keys():
            for inner_key, inner_value in value.items():
                if isinstance(inner_value, dict) and inner_key in base_dict[key].keys():
                    for k, v in inner_value.items():
                        base_dict[key][inner_key][k] = v
                else:
                    if inner_key in base_dict[key] and isinstance(base_dict[key][inner_key], list):
                        base_dict[key][inner_key].extend(inner_value)
                    else:
                        base_dict[key][inner_key] = inner_value
        else:
            base_dict[key] = value


def get_random_string(size, include_numbers=True):
    """
    Generates a random string of the specified size

    :type size: int
    :param size: The length of the random string to be returned
    :type include_numbers: bool
    :param include_numbers: Toggles whether numbers are to be included in the pool of candidate characters for the
           random string

    :return: Randomised string
    :rtype: str
    """

    if include_numbers:
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
    else:
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    temp_string = ''.join(random.choice(characters) for x in range(size))
    return ''.join(random.sample(temp_string, len(temp_string)))


def get_installed_version(package):
    """
    Returns the locally installed version for package name passed in

    :type package: str
    :param package: The name of the package to extract the version of

    :return: String version of the rpm package
    :rtype: str
    """
    global installed_versions
    if installed_versions.get(package):
        return installed_versions[package]

    log.logger.debug("Determining version of installed package: {0} (via rpm command)".format(package))
    cmd = "rpm -qa --qf '%{{version}}' {package}".format(package=package)
    response = shell.run_local_cmd(shell.Command(cmd))
    match = re.search('([0-9]*[.][0-9]*[.][0-9]*)', response.stdout)
    if match and response.stdout.count('.') == 2:
        version = match.group(1)
        installed_versions[package] = version
        return version
    log.logger.debug("Unable to determine version of installed package: {0}".format(package))
    return "Unknown"


def get_internal_file_path_for_import(root_dir, child_dir, file_name):
    """
    Return a file path from the internal package

    :param root_dir: Root internal directory to join file path from
    :type root_dir: str
    :param child_dir: Child internal directory to join file path from
    :type child_dir: str
    :param file_name: Resource to look for
    :type file_name: str

    :raises RuntimeError: raised if file path is invalid

    :return: file_path to the requested resource
    :rtype: str
    """
    try:
        _internal_data = pkgutil.get_loader('enmutils_int')
        _file_path = unipath.Path(_internal_data.filename)
        full_path = os.path.join(_file_path, root_dir, child_dir, file_name)
    except Exception as e:
        raise RuntimeError("Failed to find requested file path. Response: %s" % e.message)
    else:
        return full_path


def install_licence(user, licence_file_name):
    """
    Install a valid licence to use

    :param user: User who will install the licence on ENM
    :type user: `enm_user_2.User`
    :param licence_file_name: name of the licence to be installed
    :type licence_file_name: str

    :raises ScriptEngineResponseValidationError: raised if install command fails

    :rtype: `script_engine_2.Response`
    :return: Output returned by the cm cli
    """
    INSTALL_LICENCE_CMD = "lcmadm install file:%s"

    licence_path = get_internal_file_path_for_import("etc", "licences", licence_file_name)
    response = user.enm_execute(INSTALL_LICENCE_CMD % licence_file_name, file_in=licence_path)
    if "ERROR" in response.get_output():
        raise ScriptEngineResponseValidationError("Failed to import %s. Response was: %s"
                                                  % (licence_file_name, ','.join(response.get_output())),
                                                  response=response)

    return response.get_output()


def start_stopped_nodes_or_remove(nodes):
    """
    Checks if nodes are stopped, attempt to start any stopped nodes or remove them

    :param nodes: List of 'load_node.LoadNode' instances
    :type nodes: list

    :raises EnvironError: raised if no started nodes are available
    :raises NetsimError: raised if unable to SSH to the NetSim host
    :raises Exception: raised for any other NetSim host failure

    :rtype: list
    :return: list Nodes found to be started
    """
    removed = []
    try:
        stopped_nodes = check_nodes_started(nodes)
    except NetsimError as e:
        raise NetsimError(e.message)
    except Exception as e:
        raise Exception(e.message)
    if not stopped_nodes:
        return nodes
    power_nodes = PowerNodes(stopped_nodes)
    power_nodes.start_nodes()
    stopped_nodes = check_nodes_started(nodes)
    for node in stopped_nodes:
        removed.append(node)
        nodes.remove(node)
    if removed:
        log.logger.debug("Removed the following nodes: {0}".format(" , ".join([node.node_id for node in removed])))
    if not nodes:
        raise EnvironError("No available, started nodes. Please confirm nodes are started on respective NetSim hosts.")
    else:
        return nodes


class LimitedSizeDict(OrderedDict):
    """
    A size limited OrderedDict object
    """

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs: size_limit needed as kwarg.
        """
        self.size_limit = kwargs.pop("size_limit", None)
        OrderedDict.__init__(self, *args, **kwargs)
        self._check_size_limit()

    def __setitem__(self, key, value, **kwargs):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem()


def return_dict_from_json_artifact(version):
    """
    Build a python dict based on the provided rpm version from a nexus artifact

    :type version: str
    :param version: Version to retrieve

    :raises EnvironError: raised if the artifact fails to download from nexus

    :rtype: dict
    :return: Dictionary built from the json artifact
    """
    json = download_artifact_from_nexus('com.ericsson.dms.torutility', 'ERICtorutilitiesinternal_CXP9030579', version,
                                        'json')
    if not json:
        raise EnvironError("Failed to correctly download artifact to local environment.")
    return convert_from_json_to_dict(get_json_from_a_file(json)[0])


def filter_artifact_dict_for_profile_keys(version, network_key='basic'):
    """
    Return all the Profile name keys from the profile values, as it should contain all keys (40k by default)

    :type version: str
    :param version: Version to retrieve
    :type network_key: str
    :param network_key: network size to retrieve the keys from

    :raises EnvironError: raised if the artifact does not contain the network_key

    :rtype: set
    :return: Set of profile names based on the keys
    """
    artifact = return_dict_from_json_artifact(version)
    all_keys = []
    try:
        for key in artifact.get(network_key).iterkeys():
            all_keys.extend(artifact.get(network_key).get(key).keys())
    except (AttributeError, KeyError) as e:
        raise EnvironError("Failed to retrieve requested keys from artifact, response {0}".format(e.message))
    return set(all_keys)


def get_days_of_the_week(upper=False):
    """
    Return the days of the week

    :type upper: bool
    :param upper: Flag to return the values as uppercase

    :rtype: list
    :return: List of all days of the week
    """
    if not upper:
        return [date(2017, 5, i).strftime('%A') for i in range(1, 8)]
    return [date(2017, 5, i).strftime('%A').upper() for i in range(1, 8)]


def chunks(elements, n):
    """
    Divide a list in n-sized chunks

    :type elements: list
    :param elements: list of elements to be split into chunks
    :type n: int
    :param n: size of chunk

    :rtype: list
    :yields: chunk of elements with size n,  one by one
             (if the number of elements in chunk is less than n, all the elements in chunk will be returned)
    """
    elements = elements if elements else []
    for i in xrange(0, len(elements), n):
        yield elements[i:i + n]


def split_list_into_sublists(list_to_split, number_of_sublists):
    """
    Takes a list of object as input. Distributes the objects evenly between n lists and returns list of lists
    :param list_to_split: list to be split
    :type list_to_split: list
    :param number_of_sublists: Number of list to be created
    :type number_of_sublists: int
    :return: List of lists
    :rtype: list
    """
    lists = []

    if number_of_sublists > 0:
        quotient, remainder = divmod(len(list_to_split), number_of_sublists)
        lists = list((list_to_split[i * quotient + min(i, remainder):(i + 1) * quotient + min(i + 1, remainder)] for i
                      in xrange(number_of_sublists)))

    return [item for item in lists if item != []]


def ensure_all_daemons_are_killed():
    """
    Function to identify any workload daemon process still running, and forcefully kill the process
    """
    cmd = ('pgrep -f "(/opt/ericsson/enmutils|{0}/bladerunners|/root/bladerunners).*daemon.*([A-Z]_[A-Z]|[A-Z]_[0-9])"'
           .format(STORAGE_DIR))
    response = shell.run_local_cmd(cmd)
    all_daemons = [pid for pid in response.stdout.split("\n") if pid and pid.isdigit()]
    log.logger.debug("Killing the following processes: [{0}]".format(", ".join(all_daemons)))
    for process_id in all_daemons:
        try:
            process.kill_process_id(int(process_id), signal.SIGKILL)
        except Exception as e:
            msg = ("Failed to force kill process [{0}], response: [{1}], manual intervention may be required."
                   .format(process_id, str(e)))
            log.logger.info(msg)
            continue
    log.logger.debug("Completed daemon process clean up operation.")


def check_if_upgrade_in_progress_physical_deployment():
    """
    Check for active upgrade

    :return: Boolean indicating if an upgrade is in progress
    :rtype: bool
    """
    log.logger.debug("Checking for active upgrade.")
    if check_for_existing_process_on_ms("upgrade_enm").ok or check_for_existing_process_on_ms("enm_snapshots").ok:
        log.logger.debug("Active upgrade process found.")
        return True
    if filesystem.does_file_exist_on_ms('/ericsson/enm/dumps/.upgrade_ongoing'):
        log.logger.debug("Upgrade currently in progress.")
        return True
    else:
        log.logger.debug("No active upgrade in progress.")
        return False


def check_for_active_litp_plan():
    """
    Check for active LITP plan

    :return: Boolean indicating if a litp plan is active
    :rtype: bool
    """
    log.logger.debug("Checking for active LITP plan")
    response = shell.run_cmd_on_ms(shell.Command('/usr/bin/python /usr/bin/litp show -p /plans/plan -o state'))
    if "Plan does not exist" in response.stdout:
        log.logger.debug("No LITP plan exists.")
        return False
    elif 'successful' not in response.stdout:
        log.logger.debug("LITP plan currently active.")
        return True
    else:
        log.logger.debug("LITP plan not currently active.")
        return False


def check_for_backup_in_progress():
    """
    Check if backup is currently in progress

    :return: Boolean value of the returned response object
    :rtype: bool
    """
    # Check for backup snapshot
    log.logger.debug("Starting check for backup in progress.")
    response = shell.run_cmd_on_ms(shell.Command('/opt/ericsson/enminst/bin/enm_snapshots.bsh --action list_snapshot'))
    if 'ombs' in response.stdout:
        log.logger.debug("Backup snapshots currently on deployment.")
        return response.ok
    # Check for backup log on the LMS
    response = shell.run_cmd_on_ms(shell.Command('find /opt/ericsson/itpf/bur/log/bos/ -mmin -2 -type f -print'))
    if 'bos.log' in response.stdout:
        log.logger.debug("Backup log is currently active on deployment.")
        return response.ok
    # Check for already running db_backup process
    if check_for_existing_process_on_ms('backup_database').ok:
        log.logger.debug("Backup process currently active on deployment.")
        return True
    else:
        log.logger.debug("No active backup in progress.")
        return False


def check_for_existing_process_on_ms(process_to_check):
    """
    Simple check for an existing process

    :param process_to_check: Process name or pattern to be passed to pgrep
    :type process_to_check: str

    :return: a shell.response object containing the results of issuing the command
    :rtype: shell.Response
    """
    log.logger.debug("Starting check for process {0}".format(process_to_check))
    response = shell.run_cmd_on_ms(shell.Command('pgrep -f {0}'.format(process_to_check)))
    log.logger.debug("Completed check for process {0}".format(process_to_check))
    return response


def delete_profile_users(profile_name):
    """
    Delete all users in ENM matching the supplied profile

    :param profile_name: ProfileName to use to locate the list of user objects
    :type profile_name: str
    """
    try:
        user_names = User.get_usernames(user=get_workload_admin_user())
    except Exception as e:
        log.logger.debug("Failed to retrieve user list, response was: {0}".format(str(e)))
        return

    for _ in user_names:
        if re.match(re.compile("^{0}_".format(profile_name.strip())), _):
            user = User(_)
            try:
                # change to workload admin when delivered
                user.delete(delete_as=get_workload_admin_user())
            except Exception as e:
                log.logger.debug("Failed to delete user [{0}], response was: {1}".format(_, str(e)))
    log.logger.debug("Successfully removed all {0} users.".format(profile_name))


def create_users_operation(identifier, number, roles, fail_fast=True, safe_request=False, retry=False, level=1):
    """
    Manages the creation of the requested user(s)

    :type identifier: str
    :param identifier: Str which will act as the user name
    :type number: int
    :param number: number of users to create
    :type roles: list
    :param roles: list of roles to give to users
    :type fail_fast: bool
    :param fail_fast: exit execution if user fails to create
    :type safe_request: bool
    :param safe_request: Ignore certain requests exceptions
    :type retry: bool
    :param retry: retry until a user is created
    :param level: Integer to track the recursive level
    :type level: int

    :return: list of created enm_user objects, list of failed enm user objects
    :rtype: tuple

    :raises EnmApplicationError: if error creating user and fail_fast is True
    """
    users_list = []
    failed_users = []
    admin_user = None
    for i in xrange(number):
        user = User("{0}_u{1}".format(identifier, i), "TestPassw0rd", roles=roles, safe_request=safe_request,
                    persist=True, keep_password=True)
        try:
            admin_user = admin_user or get_workload_admin_user()
            user.create(create_as=admin_user)
            users_list.append(user)
        except Exception as e:
            log.logger.debug("Error creating user in {0}: Exception: {1}".format(identifier, str(e)))
            if fail_fast:
                raise EnmApplicationError(str(e))
            failed_users.append(user)
    if not users_list and retry and level < 10:
        sleep_delay = 120 if level < 5 else 60 * level
        log.logger.debug("Failed to create users, sleeping for {} seconds before retrying.".format(sleep_delay))
        time.sleep(sleep_delay)
        failed_users = []
        level += 1
        users_list, failed_users = create_users_operation(identifier, number, roles, fail_fast=fail_fast,
                                                          safe_request=safe_request, retry=retry, level=level)
    return users_list, failed_users


def add_profile_to_active_workload_profiles(profile_name):
    """
    Adds profile name to the active_workload_profile set.
    :param profile_name: Name of profile to add to set.
    :type profile_name: str
    """
    log.logger.debug('Adding {0} to active_workload_profiles list')
    with mutexer.mutex("workload_profile_list", persisted=True):
        active_profiles = persistence.get("active_workload_profiles")
        active_profiles.add(profile_name)
        persistence.set("active_workload_profiles", active_profiles, -1)


def remove_profile_from_active_workload_profiles(profile_name):
    """
    Remove profile from active_workload_profiles.
    :param profile_name: Name of profile to remove if present in set.
    :type profile_name: str
    """
    with mutexer.mutex("workload_profile_list", persisted=True):
        active_profiles = persistence.get("active_workload_profiles")
        if profile_name in active_profiles:
            log.logger.debug('Removing {0} from active_workload_profiles list'.format(profile_name))
            active_profiles.remove(profile_name)
            persistence.set("active_workload_profiles", active_profiles, -1)


def terminate_user_sessions(profile_name):
    """
    Function to logout and close session(s) users matching the supplied profile name

    :param profile_name: Name of the profile to match
    :type profile_name: str
    """
    if profile_name in EXCLUDED_PROFILES:
        return
    try:
        log.logger.debug("Fetching list of user(s) currently in ENM.")
        user = get_workload_admin_user()
        usernames = user.get_usernames()
        profile_users = [username for username in usernames if re.split(r'_\d+-', username)[0] == profile_name]
        log.logger.debug("Found total user(s) currently in ENM with an open session: {0}.".format(len(profile_users)))
    except Exception as e:
        log.logger.debug("Failed to get ENM user session information, error encountered: {0}.".format(str(e)))
        profile_users = []
    for profile_user in profile_users:
        try:
            user_session_key = "{0}_session".format(profile_user)
            if persistence.has_key(user_session_key):
                user_session = persistence.get(user_session_key)
                log.logger.debug("Attempting to remove session for username: {0}.".format(profile_user))
                user_session.remove_session()
                log.logger.debug("Removed session for username: {0}.".format(profile_user))
        except Exception as e:
            log.logger.debug("Failed to remove ENM user session, error encountered: {0}.".format(str(e)))
    log.logger.debug("Completed ENM user session termination check.")
