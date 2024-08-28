import datetime
import syslog
import time

from functools import partial
from gc import collect
from math import ceil
from random import randint
import pexpect
from paramiko import SSHException

from enmutils.lib import cache, log, mutexer, filesystem, shell, multitasking
from enmutils.lib.exceptions import EnvironError, EnmApplicationError, TimeOutError
from enmutils.lib.filesystem import does_file_exist
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.pm_nbi import Fls
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow, get_matched_supported_datatypes_with_configured_datatypes
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_list_of_scripting_service_ips
from retrying import retry


def safe_teardown(profile, kill_running_sftp_processes, sftp_pids_file, clear_nbi_dir):
    """
    Pm_26 teardown method which will kill the running sftp threads.

    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :param kill_running_sftp_processes: Cmd to kill the running sftp processes
    :type kill_running_sftp_processes: str
    :param sftp_pids_file: Running sftp pids
    :type sftp_pids_file: str
    :param clear_nbi_dir: Cmd to delete retrieved files
    :type clear_nbi_dir: str
    """
    if cache.is_host_physical_deployment():
        shell.run_cmd_on_ms(shell.Command(kill_running_sftp_processes % sftp_pids_file, allow_retries=False))
        shell.run_cmd_on_ms(shell.Command('>%s' % sftp_pids_file, allow_retries=False))
        shell.run_cmd_on_ms(shell.Command(clear_nbi_dir))
        shell.run_cmd_on_ms(shell.Command("pkill -f 'ssh.*{0}'".format(profile.NAME)))
    else:
        shell.run_local_cmd(shell.Command(kill_running_sftp_processes % sftp_pids_file, allow_retries=False))
        shell.run_local_cmd(shell.Command('>%s' % sftp_pids_file, allow_retries=False))
        shell.run_local_cmd(shell.Command("pkill -f 'ssh.*{0}'".format(profile.NAME)))
    shell.run_local_cmd(shell.Command(clear_nbi_dir))


# Thread functions

def tq_task_executor(task_set, profile):
    """
    Handles the thread queue task set by calling the correct function

    :param task_set: Tuple containing Task to call e.g.
        1) function_name=sftp_nbi_files, function_arg1="batch filename", function_arg2="scripting VM IP",
        function_arg3="username"or
        2) function_name=monitor_sftp_file_transfer, function_arg1="dictionary of times", function_arg2="username",
        function_arg3=""
    :type task_set: tuple
    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    """
    function_name, function_arg1, function_arg2, function_arg3 = task_set
    function_name(function_arg1, function_arg2, function_arg3, profile)


@retry(retry_on_exception=lambda e: isinstance(e, EnmApplicationError), wait_fixed=5000, stop_max_attempt_number=2)
def sftp_nbi_files(batch_filename, scripting_service_ip, username, profile):
    """
    Sftp pm files to NBI

    :param batch_filename: Sftp batch filename.
    :type batch_filename: str
    :param scripting_service_ip: IP address of scripting VM.
    :type scripting_service_ip: str
    :param username: User Name
    :type username: str
    :param profile: PM_26 object. Profile instance.
    :type profile: Pm26Profile

    :raises EnvironError: Exception raised if sftp process encounters "Permission denied"
    :raises EnmApplicationError: Exception raised if sftp process encounters "Connection reset by peer"
    """
    log.logger.debug("Executing sftp command towards Scripting VM IP '{0}' using file '{1}'"
                     .format(scripting_service_ip, batch_filename))

    start_time_offset = int(batch_filename[-1]) if (isinstance(batch_filename[-1], int)) else randint(0, 9)
    log.logger.debug("Sleeping for {0}s to stagger connection attempts".format(start_time_offset))
    time.sleep(start_time_offset)

    batch_files_count = len(filesystem.read_lines_from_file(batch_filename))
    log.logger.debug("{0} batch files count: {1}".format(batch_filename, batch_files_count))
    failure_message = "In {0} file, failed to transfer {1} files.".format(batch_filename, batch_files_count)

    sftp_command = profile.SFTP_FILES_TO_NBI_COMMAND.format(
        sftp_command_timeout=profile.time_remaining_for_sftp,
        basic_ssh_options=profile.SSH_BASIC_OPTIONS,
        identity_file=profile.KEYPAIR_FILE_ON_WLVM,
        batch_filename=batch_filename,
        username=username,
        scripting_service_ip=scripting_service_ip,
        sftp_pids_file=profile.SFTP_PIDS_FILE.format(username=username))
    if cache.is_host_physical_deployment():
        cmd_response = shell.run_cmd_on_ms(shell.Command(sftp_command, allow_retries=False,
                                                         timeout=profile.time_remaining_for_sftp))
    else:
        cmd_response = shell.run_local_cmd(shell.Command(sftp_command, allow_retries=False,
                                                         timeout=profile.time_remaining_for_sftp))
    if "Permission denied" in cmd_response.stdout:
        profile.nbi_transfer_stats[username]['missed_file_count'][batch_filename] = batch_files_count
        log.logger.debug(failure_message)
        profile.add_error_as_exception(EnvironError(failure_message))
        raise EnvironError("'Permission denied' encountered while sftp'ing files from {0} which could mean "
                           "profile user is not authorized to 1) access scripting VM, or "
                           "2) access files on the PMIC mountpoints on the NAS.".format(scripting_service_ip))

    elif "Connection reset by peer" in cmd_response.stdout:
        profile.nbi_transfer_stats[username]['missed_file_count'][batch_filename] = batch_files_count
        log.logger.debug(failure_message)
        profile.add_error_as_exception(EnmApplicationError(failure_message))
        log.logger.debug("Unable to connect to {0} on this attempt - will stop retrying after a number of attempts"
                         .format(scripting_service_ip))
        raise EnmApplicationError("Connection reset by peer ({0})".format(scripting_service_ip))

    elif "Couldn't stat remote file" in cmd_response.stdout:
        profile.nbi_transfer_stats[username]['missed_file_count'][batch_filename] = batch_files_count
        log.logger.debug(failure_message)
        profile.add_error_as_exception(EnvironError(failure_message))
        raise EnvironError("Unable to find files via scripting VM ({0})".format(scripting_service_ip))

    elif cmd_response.rc != 0:
        profile.nbi_transfer_stats[username]['missed_file_count'][batch_filename] = batch_files_count
        log.logger.debug(failure_message)
        profile.add_error_as_exception(EnvironError(failure_message))
        raise EnvironError("Error occurred during sftp of files from {0} - see log for details"
                           .format(scripting_service_ip))

    log.logger.debug("Execution of sftp command towards Scripting VM IP '{0}' using file '{1}' "
                     "with {2} files is finished" .format(scripting_service_ip, batch_filename, batch_files_count))


def monitor_sftp_file_transfer(collection_times, username, _, profile):
    """
    Monitors sftp pid activity and regularly clears the pm_nbi file storage dir (/dev/shm/PM_NBI/)

    :param collection_times: Dictionary containing various timings related to the iteration
    :type collection_times: dict
    :param username: User Name
    :type username: str
    :param _: blank
    :type _: str
    :param profile: PM_26 Profile object
    :type profile: Pm26Profile

    :raises EnvironError: Raises exception if file collection hasnt completed at end of monitoring

    :return: Indicates success or otherwise if all sftp processes completed normally
    :rtype: bool

    """
    sftp_process_checking_interval = 10
    buffer_time_to_complete_profile_tasks = 60

    start_time_of_thread = time.time()

    time_elapsed_since_start_of_iteration = int(datetime.datetime.now().time().strftime('%s')) - int(datetime.datetime.strptime(collection_times['end'],
                                                                                                                                '%Y-%m-%dT%H:%M:%S').time().strftime('%s'))
    time_remaining_for_iteration = ((collection_times['rop_interval'] * 60) - time_elapsed_since_start_of_iteration -
                                    buffer_time_to_complete_profile_tasks)
    log.logger.debug('time remaining for iteration {0} secs'.format(time_remaining_for_iteration))
    possible_number_of_checks = int(ceil(time_remaining_for_iteration / sftp_process_checking_interval))

    sftp_complete = check_that_sftp_processes_are_complete(profile, username, start_time_of_thread,
                                                           sftp_process_checking_interval, possible_number_of_checks, time_remaining_for_iteration)

    if not sftp_complete and any_sftp_processes_still_running("Final", profile, username, start_time_of_thread):
        log.logger.debug("Monitor thread: Fetching of PM Files has not completed within the ROP time"
                         " - killing the sftp processes now before the next iteration starts")
        safe_teardown(profile, profile.KILL_RUNNING_SFTP_PROCESSES.format(username=username),
                      profile.SFTP_PIDS_FILE.format(username=username),
                      profile.REMOVE_NBI_USER_DIR.format(username=username))
        raise EnvironError("File fetching not completed within expected time "
                           "- sftp processes were killed by monitor thread to avoid overlap with transfer of files "
                           "for next ROP")

    return sftp_complete


def check_that_sftp_processes_are_complete(profile, username, start_time_of_thread, sftp_process_checking_interval,
                                           number_of_checks_to_perform, time_remaining_for_iteration):
    """
    Check that sftp processes are complete

    The function will check every x seconds to determine if the sftp processes are no longer running.
    If they are still running then it means that file transfer is still ongoing.

    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :param username: User Name
    :type username: str
    :param start_time_of_thread: Epoch time
    :type start_time_of_thread: float
    :type sftp_process_checking_interval: Interval of seconds between checks
    :param sftp_process_checking_interval: int
    :param number_of_checks_to_perform: Number of checks to perform
    :type number_of_checks_to_perform: int
    :param time_remaining_for_iteration: Time remaining for iteration
    :type time_remaining_for_iteration: int
    :return: True if all processes are complete, otherwise False
    :rtype: bool
    """
    log.logger.debug("Monitor thread: Checking that sftp process are complete")

    for checkpoint_number in range(1, number_of_checks_to_perform):
        # Want to sleep only for the amount of time that it takes to get to the next checkpoint
        current_time = time.time()
        sleep_until_next_check = ((start_time_of_thread + (sftp_process_checking_interval * checkpoint_number)) -
                                  current_time)

        if sleep_until_next_check > 0:
            log.logger.debug("Monitor thread: Sleeping until the next checkpoint ({0}s apart)"
                             .format(sftp_process_checking_interval))
            time.sleep(sleep_until_next_check)
        else:
            log.logger.debug("Unexpected situation encountered: There is a delay in code execution. "
                             "The current time ({0}) should ideally have been within {1}s of last check. "
                             "This problem may be related to a potential IO contention issue on this server."
                             "Check 'sar' command to investigate".format(current_time, sftp_process_checking_interval))
        later_time = time.time() - current_time
        time_remaining_for_iteration = time_remaining_for_iteration - later_time
        log.logger.debug('inside monitor and time remaining for iteration '
                         'is {0} mins'.format(time_remaining_for_iteration / 60))
        if not any_sftp_processes_still_running(str(checkpoint_number), profile, username, start_time_of_thread):
            return True
        elif time_remaining_for_iteration <= 60:
            return False


def any_sftp_processes_still_running(checkpoint_indicator, profile, username, start_time_of_thread):
    """
    Check status of sftp processes running on server.

    :param checkpoint_indicator: Indicates what check is being performed
    :type checkpoint_indicator: str
    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :param username: User Name
    :type username: str
    :param start_time_of_thread: Epoch Time when the thread was started
    :type start_time_of_thread: float
    :return: True if sftp proceses are running
    :rtype: bool
    :raises EnvironError: if problem occurs while checking process status
    """
    log.logger.debug("Monitor thread - Checkpoint {0}: Checking if all sftp processes have completed"
                     .format(checkpoint_indicator))

    try:
        if cache.is_host_physical_deployment():
            sftp_pids_status = shell.run_cmd_on_ms(shell.Command(
                profile.CHECK_FOR_RUNNING_SFTP_PROCESSES.format(username=username), log_cmd=False)).stdout.split()
        else:
            sftp_pids_status = shell.run_local_cmd(shell.Command(
                profile.CHECK_FOR_RUNNING_SFTP_PROCESSES.format(username=username), log_cmd=False)).stdout.split()
    except Exception as e:
        raise EnvironError("Error checking if processes are still running - {0}".format(str(e)))

    log.logger.debug("Monitor thread - PID Status ('0' means sftp process still running): {0}"
                     .format(sftp_pids_status))

    if "0" not in sftp_pids_status:
        log.logger.debug("Monitor thread: All sftp processes are no longer running")
        profile.nbi_transfer_stats[username]["nbi_transfer_time"] = time.time() - start_time_of_thread
        return False
    log.logger.debug("Monitor thread: Some sftp processes are still running - continuing to wait")
    return True


def perform_sftp_transfer_tasks(fls_tuple, profile):
    """
    Perform Transfer tasks.

    :param fls_tuple: FLS object and sleep time
    :type fls_tuple: Tuple
    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    """
    fls, sleep_time = fls_tuple
    log.logger.debug("SLeeping for {0}sec".format(sleep_time))
    time.sleep(sleep_time)
    log.logger.debug("Transfer tasks - Started")
    collection_times = profile.set_collection_times(fls.user.username)
    iteration_success = False
    try:
        profile.check_pm_nbi_directory(fls.user.username)
        iteration_success = profile.transfer_pmic_files_to_nbi(fls, collection_times)
        log.logger.debug("File Transfer operation completed")
    except Exception as e:
        profile.add_error_as_exception(e)

    if not iteration_success:
        profile.add_error_as_exception(EnvironError("File Transfer did not complete successfully "
                                                    "- check profile log for more details"))
    log.logger.debug("Transfer tasks - Finished")
    collect()
    profile.check_profile_memory_usage()


class PmFlsNbiProfile(GenericFlow):

    FETCH_ROP_AGE_NUMBER = 1  # ROP being fetched is X number of ROP's ago from current ROP
    USER_ROLES = None
    NUM_USERS = 1
    N_SFTP_THREADS = 10
    DATA_TYPES = []
    PM_NBI_DIR = "/dev/shm/pm_nbi/{username}"  # Using tmpfs (/dev/shm) for faster storage on local system

    PM_NBI_FETCHED_PM_FILES_DIR = "/dev/null"
    PM_NBI_BATCH_FILES_DIR = "{0}/batch_files".format(PM_NBI_DIR)

    SFTP_PIDS_FILE = "{0}/pm_nbi_pids".format(PM_NBI_BATCH_FILES_DIR)
    PM_NBI_SFTP_BATCH_FILENAME = "{0}/pm_nbi_batch_".format(PM_NBI_BATCH_FILES_DIR)

    SSH_BASIC_OPTIONS = "-o LogLevel=error -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

    SFTP_FILES_TO_NBI_COMMAND = (
        "timeout {sftp_command_timeout} bash -c 'sftp {basic_ssh_options} -b {batch_filename} "
        "{username}@{scripting_service_ip} 1>/dev/null & echo $! >> {sftp_pids_file}'")

    KEYPAIR_FILE_ON_WLVM = cache.CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM
    CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_LMS = "/root/.ssh/vm_private_key"

    # bash cmd set
    KILL_RUNNING_SFTP_PROCESSES = ('cat %s | while read pid; do if [[ $(ps -p $pid -o comm=) == "sftp" ]]; '
                                   'then kill $pid; fi; done')
    CHECK_FOR_RUNNING_SFTP_PROCESSES = ('cat %s | while read pid; do ps -p $pid > /dev/null 2>&1; echo -n "$? "; done'
                                        % SFTP_PIDS_FILE)
    CLEAR_NBI_DIR_FILES = 'find %s -type f -print0 | xargs -0 -P 0 rm -f' % PM_NBI_BATCH_FILES_DIR
    REMOVE_NBI_USER_DIR = 'rm -rf %s' % PM_NBI_DIR

    DISK_USAGE_COMMAND = "du -Sh --block-size=1M %s | awk '{ print $1 }'"
    COUNT_FILES = "/bin/ls -1U %s | wc -l"

    def __init__(self):
        """
        Init Method
        """
        super(PmFlsNbiProfile, self).__init__()
        self.nbi_transfer_stats = dict()
        self.scp_scripting_service_ip_list = []
        self.active_scripting_service_ip_list = []
        self.users = []
        self.data_type_file_id_dict = {}
        self.time_remaining_for_sftp = 0
        self.is_cloud_native = None
        self.is_physical = None
        self.lms_host = None
        self.updated_available_data_types = {}

    def initiate_profile_and_environment(self):
        """
        Prepare profile and environment for profile execution

        """
        log.logger.debug("Clearing PM NBI dir related to profile")
        shell.run_local_cmd(shell.Command("{0}*".format(self.REMOVE_NBI_USER_DIR.format(username=self.NAME))))

        self.set_environment_type_attributes()

        try:
            self.users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        except Exception as e:
            raise EnmApplicationError("Cannot create users on ENM: {0}".format(e))
        fls_list = []
        for user in self.users:
            fls_list.append(Fls(user=user))

            self.teardown_list.append(partial(safe_teardown, self,
                                              self.KILL_RUNNING_SFTP_PROCESSES.format(username=user.username),
                                              self.SFTP_PIDS_FILE.format(username=user.username),
                                              self.REMOVE_NBI_USER_DIR.format(username=user.username)))
            self.clear_sftp_pid_file(user.username)
        sleep_time = range(0, len(fls_list) * 20, 20)
        fls_tuple_list = zip(fls_list, sleep_time)
        return fls_tuple_list

    def set_environment_type_attributes(self):
        """

        Set profile attributes depending on the environment type.

        """
        self.scp_scripting_service_ip_list = get_list_of_scripting_service_ips()

        if not self.scp_scripting_service_ip_list:
            raise EnvironError("The scripting_service_IPs are not set in the global.properties on ENM therefore the "
                               "profile will be unable to sftp PM files from ENM without those being set")

    def check_pm_nbi_directory(self, username):
        """
        Check whether the PM NBI directory exists; create it if missing.

        :param username: User Name
        :type username: str

        """
        log.logger.debug("Checking to see if PM NBI directory exist on Workload VM: {0}"
                         .format(self.PM_NBI_BATCH_FILES_DIR.format(username=username)))
        pm_directory = self.PM_NBI_BATCH_FILES_DIR.format(username=username)
        if not filesystem.does_dir_exist(pm_directory):
            log.logger.debug("Creating directory as it does not exist: {0}".format(pm_directory))
            shell.run_local_cmd(shell.Command('mkdir -p {0}'.format(pm_directory)))

        log.logger.debug("PM Directory checks completed")
        self.check_profile_memory_usage()

    def clear_pm_nbi_directory(self, username):
        """
        Clean the PM NBI directory

        :param username: User Name
        :type username: str
        :raises EnvironError: if unable to clear out the files stored in the NBI dir (in Shared Memory)
        """
        response = shell.run_local_cmd(shell.Command(self.CLEAR_NBI_DIR_FILES.format(username=username)))
        if not response.ok:
            raise EnvironError("Failed to remove previously fetched files - {0}".format(response.stdout))
        if cache.is_host_physical_deployment():
            response = shell.run_cmd_on_ms(shell.Command(self.CLEAR_NBI_DIR_FILES.format(username=username)))
            if not response.ok:
                raise EnvironError("Failed to remove previously fetched files - {0}".format(response.stdout))

    def clear_sftp_pid_file(self, username):
        """
        Clear the file containing sftp pids

        :param username: User Name
        :type username: str
        """
        sftp_file_path = self.SFTP_PIDS_FILE.format(username=username)
        if does_file_exist(sftp_file_path):
            shell.run_local_cmd(shell.Command(r">{0}".format(sftp_file_path)))
            if cache.is_host_physical_deployment():
                shell.run_cmd_on_ms(shell.Command(">%s" % sftp_file_path))

    def get_active_scripting_service_ip_list(self):
        """
        Determine the list of active Scripting Service VM's from the available ones

        :return: List of active Scripting Service VM IP's
        :rtype: list

        :raises EnvironError: if active Scripting Service VM's are not found.
        """
        log.logger.debug("Trying to determine which scripting service VM's are active from available IP's: {0}"
                         .format(self.scp_scripting_service_ip_list))

        active_scripting_service_ip_list = []
        profile_username = self.users[0].username

        for ip_address in self.scp_scripting_service_ip_list:
            if self.are_ssh_credentials_valid(ip_address, user=profile_username, password="TestPassw0rd"):
                active_scripting_service_ip_list.append(ip_address)
                log.logger.debug(
                    "Login with {0} from Workload VM was successful towards the following Scripting Service "
                    "IP's: {1}".format(profile_username, active_scripting_service_ip_list))
            else:
                log.logger.debug("Unable to login with cloud-user from Workload VM to Scripting Service IP: {0}"
                                 .format(ip_address))

        self.check_profile_memory_usage()
        if active_scripting_service_ip_list:
            return active_scripting_service_ip_list
        else:
            raise EnvironError("{0} scripting service VM's are not active. "
                               "Profile will be unable to sftp PM files from "
                               "ENM".format(", ".join(self.scp_scripting_service_ip_list)))

    def cleanup_pm_nbi_profile_artefacts(self, fls):
        """
        Perform cleanup of PM NBI Profile artefacts

        :param fls: Fls object to create batch files.
        :type fls: enmutils_int.lib.pm_nbi.Fls

        :raises EnvironError: exception raised if there is a problem is with the Environment
        """
        log.logger.debug("1. Performing cleanup")
        try:
            log.logger.debug("Clearing the PM NBI dir on the Workload VM: {0}"
                             .format(self.PM_NBI_BATCH_FILES_DIR.format(username=fls.user.username)))
            self.clear_pm_nbi_directory(fls.user.username)

            log.logger.debug("Clearing sftp monitor pid file")
            self.clear_sftp_pid_file(fls.user.username)
        except Exception as e:
            failure_reason = "Exception encountered during cleanup: {0}".format(str(e))
            raise EnvironError("{0} - {1}".format(failure_reason, str(e)))

        self.check_profile_memory_usage()

    def get_list_of_files_from_fls(self, fls, collection_times):
        """
        Get list of files from FLS

        :param fls: Fls object to create batch files.
        :type fls: enmutils_int.lib.pm_nbi.Fls
        :param collection_times: Dictionary of times related to this iteration.
        :type collection_times: dict
        :return: List of files
        :rtype: list

        :raises EnvironError: exception raised if there is a problem is with the Environment
        :raises EnmApplicationError: exception raised if there is a problem is with the ENM application
        """
        log.logger.debug("2. Querying FLS to discover files to be collected")
        log.logger.debug("data type file id dict before FLS query: {0}".format(self.data_type_file_id_dict))
        try:
            files_to_collect, self.data_type_file_id_dict = multitasking.create_single_process_and_execute_task(get_files_to_collect,
                                                                                                                args=(self, fls),
                                                                                                                fetch_result=True)
        except Exception as e:
            failure_reason = "Exception encountered while querying FLS to determine list of files to be collected"
            raise EnmApplicationError("{0} - {1}".format(failure_reason, str(e)))

        log.logger.debug("data type file id dict after FLS query: {0}".format(self.data_type_file_id_dict))
        if not files_to_collect:
            failure_reason = ("FLS has reported that no files exists for this ROP "
                              "- see profile log for details of FLS queries performed")
            raise EnvironError("{0}".format(failure_reason))
        collect()
        self.check_profile_memory_usage()
        return files_to_collect

    def create_sftp_batch_files_on_server(self, fls, files_to_collect):
        """
        Create sftp batch files on server to be used to fetch the files

        :param fls: Fls object to create batch files.
        :type fls: enmutils_int.lib.pm_nbi.Fls
        :param files_to_collect: List of files
        :type files_to_collect: list

        :raises EnvironError: exception raised if there is a problem is with the Environment
        """
        log.logger.debug("3. Creating sftp batch files in {}"
                         .format(self.PM_NBI_BATCH_FILES_DIR.format(username=fls.user.username)))

        log.logger.debug("Number of PM files to be collected as reported by FLS: {}".format(len(files_to_collect)))
        with mutexer.mutex("nbi_transfer_stats"):
            self.nbi_transfer_stats[fls.user.username]["nbi_fls_file_count"] += len(files_to_collect)
            log.logger.debug("nbi_transfer_stats: {0}".format(self.nbi_transfer_stats))

        pm_nbi_batch_filename_prefix = self.PM_NBI_SFTP_BATCH_FILENAME.format(username=fls.user.username) + "{:02d}"

        try:
            fls.create_sftp_batch_files(data=files_to_collect,
                                        pm_nbi_dir=self.PM_NBI_FETCHED_PM_FILES_DIR,
                                        pm_nbi_batch_filename_prefix=pm_nbi_batch_filename_prefix,
                                        num_of_sftp_batch_files=self.N_SFTP_THREADS,
                                        shuffle_data=True)
        except Exception as e:
            failure_reason = "Exception encountered while creating sftp batch files"
            raise EnvironError("{0} - {1}".format(failure_reason, str(e)))

    def perform_sftp_fetch(self, fls, collection_times):
        """
        Create and execute threads to perform the sftp fetch operations

        :param fls: Fls object to create batch files.
        :type fls: enmutils_int.lib.pm_nbi.Fls
        :param collection_times: Dictionary of times related to this iteration.
        :type collection_times: dict
        :return: Boolean to indicate if there was exceptions during thread execution or not
        :rtype: bool

        :raises EnvironError: exception raised if there is a problem is with the Environment
        """
        log.logger.debug("4. Spawning threads to perform the sftp fetch and storage of PM files in PM NBI dir: {0}"
                         .format(self.PM_NBI_FETCHED_PM_FILES_DIR))
        try:
            fetch_end_time = int(datetime.datetime.now().time().strftime('%s')) - int(datetime.datetime.strptime(collection_times['end'],
                                                                                                                 '%Y-%m-%dT%H:%M:%S').time().strftime('%s'))
            self.time_remaining_for_sftp = (15 * 60) - fetch_end_time - 60
            log.logger.debug('time remaining for sftp {0} min'.format(self.time_remaining_for_sftp / 60))
            return multitasking.create_single_process_and_execute_task(
                create_and_execute_sftp_threads, args=(self, fls, collection_times), fetch_result=True, timeout=self.time_remaining_for_sftp)
        except Exception as e:
            failure_reason = "Exception encountered while executing threads (sftp fetch & monitor)"
            raise EnvironError("{0} - {1}".format(failure_reason, str(e)))

    def transfer_pmic_files_to_nbi(self, fls, collection_times):
        """
        Find the default PM storage of PMIC rop files and transfer them to NBI.

        :param fls: Fls object to create batch files.
        :type fls: enmutils_int.lib.pm_nbi.Fls
        :param collection_times: Dictionary of times related to this iteration.
        :type collection_times: dict
        :return: True (if method doesn't raise any error) or raises EnvironError
        :return: Boolean to indicate if there was exceptions during thread execution or not
        :rtype: bool

        """
        iteration_success = True
        self.cleanup_pm_nbi_profile_artefacts(fls)
        list_of_files = self.get_list_of_files_from_fls(fls, collection_times)
        if list_of_files and not len(list_of_files) <= len(self.updated_available_data_types):
            self.create_sftp_batch_files_on_server(fls, list_of_files)
            if cache.is_host_physical_deployment():
                self.transfer_batch_files_to_ms()
            time.sleep(60)
            iteration_success = self.perform_sftp_fetch(fls, collection_times)
        if not list_of_files:
            iteration_success = False
        return iteration_success

    def transfer_batch_files_to_ms(self):
        try:
            cmd = "scp -r -o stricthostkeychecking=no {SRC_DIR} root@{IP}:/dev/shm/".format(SRC_DIR="/dev/shm/pm_nbi/",
                                                                                            IP=cache.get_ms_host())
            shell.run_local_cmd(cmd)
        except (RuntimeError, SSHException) as e:
            raise EnvironError("Encountered exception while trying to copy the file, Exception:{0}".format(e))
        except Exception as e:
            raise EnmApplicationError(str(e))

    def log_results_of_nbi_transfer(self, iteration_success, collection_times, username):
        """
        Log the results of the sftp operation
        Logging is happening to daemon logs, via separate lines per instrumentation value,
        and to syslog (i.e. /var/log/messages file), via 1 line with all results in 1 line.

        :param iteration_success: Show whether the sftp operation was successful (True) or unsuccessful (False)
        :type iteration_success: bool
        :param collection_times: Dictionary containing times related to the NBI fetch
        :type collection_times: dict
        :param username: Username
        :type username: str
        """
        results_identifier_text = "NBI File Transfer Results for user {0}:".format(username)
        started_at_time = datetime.datetime.fromtimestamp(collection_times['start_time_of_iteration'])
        start_time = collection_times['start']
        end_time = collection_times['end']
        missed_files_count = 0

        transfer_started_at_time_text = "STARTED_AT: {}".format(started_at_time)
        collected_rop_text = "COLLECTED_ROP: {0} -> {1}".format(start_time, end_time)

        with mutexer.mutex("nbi_transfer_stats"):
            nbi_transfer_stats = self.nbi_transfer_stats[username]

        fls_file_count_text = "FLS_FILE_COUNT: {0}".format(nbi_transfer_stats["nbi_fls_file_count"])

        # Updating the transfer failed files count in missed_files_count, when iteration_success value is False
        if not iteration_success:
            for _, batch_file_count in nbi_transfer_stats['missed_file_count'].iteritems():
                missed_files_count += batch_file_count
            if not missed_files_count:
                missed_files_count = nbi_transfer_stats["nbi_fls_file_count"]

        missed_file_count_text = "MISSED_FILE_COUNT: {0}".format(missed_files_count)
        transfer_file_count_text = ("TRANSFERRED_FILE_COUNT: {0}"
                                    .format(nbi_transfer_stats["nbi_fls_file_count"] - missed_files_count))

        file_count_text = "{0}, {1}, {2}".format(fls_file_count_text, transfer_file_count_text,
                                                 missed_file_count_text)
        time_taken_mins, time_taken_secs = divmod(time.time() - collection_times['start_time_of_iteration'], 60)
        transfer_time_taken_text = ("TIME_TAKEN: {0:02.0f}:{1:02.0f} mins:secs".format(time_taken_mins, time_taken_secs))

        extra_text = ""
        if not iteration_success:
            extra_text = "Note: Failures occurred - Check profile log for more details, "

        transfer_result_text = "{0}SUCCESS: {1}".format(extra_text, iteration_success)

        instrumentation_data = ("{0}, {1}, {2}, {3}, {4}"
                                .format(collected_rop_text, transfer_started_at_time_text,
                                        file_count_text, transfer_time_taken_text, transfer_result_text))

        info_to_be_logged = "{0} {1}- {2}".format(self.NAME, results_identifier_text, instrumentation_data)
        note = ("Note: NBI Transfer stats (data & file amounts) are approximate values only. "
                "This is because of the nature of how these values are counted:- "
                "Every minute, once these values are calculated, the fetched files are wiped from the virtual memory "
                "storage to make space for more files, without eating up resources of the server where the profile "
                "is running. During this time files are still being fetched in between the running of the commands "
                "which calculate these values, leading to possible gaps")

        log.logger.debug(note)
        # Log results to profile daemon log
        log.logger.debug(info_to_be_logged)

        # Log results to syslog file as per TORF-188445
        syslog.syslog(info_to_be_logged)

    def set_collection_times(self, username):
        """
        Define the range timestamps of current iteration.

        The start & end times are being calculated to correspond with actual ROP times and to ensure that all files that
        are expected to be stored on ENM, are done so well in advance of the NBI sftp fetch time.

        :param username: Username
        :type username: str
        :return: times: Contains the start time, end time (for output) and range (for Fls query)
        :rtype: dict
        """
        log.logger.debug("Calculating ROP times to be used for performing FLS queries")
        with mutexer.mutex("nbi_transfer_stats"):
            self.nbi_transfer_stats[username] = {"nbi_transfer_time": 0, "nbi_fls_file_count": 0,
                                                 "missed_file_count": {}}

        times = {}

        current_timestamp_secs = int(time.time())
        current_local_time = datetime.datetime.fromtimestamp(current_timestamp_secs)
        current_rop_offset_from_current_localtime_mins = int(current_local_time.strftime("%M")) % self.ROP_INTERVAL
        current_rop_offset_from_current_localtime_secs = int(current_local_time.strftime("%S"))

        dst_offset_for_fetched_rop_mins = self.calculate_dst_offset_for_fetched_rop(current_timestamp_secs)

        fetched_rop_offset_from_current_local_time_mins = ((self.ROP_INTERVAL * self.FETCH_ROP_AGE_NUMBER) +
                                                           current_rop_offset_from_current_localtime_mins +
                                                           dst_offset_for_fetched_rop_mins)
        start_timestamp = (current_local_time -
                           datetime.timedelta(minutes=fetched_rop_offset_from_current_local_time_mins) -
                           datetime.timedelta(seconds=current_rop_offset_from_current_localtime_secs))

        end_timestamp = start_timestamp + datetime.timedelta(minutes=self.ROP_INTERVAL)

        times['start_time_of_iteration'] = current_timestamp_secs
        times['start'] = start_timestamp.strftime("%Y-%m-%dT%H:%M:00")
        times['end'] = end_timestamp.strftime("%Y-%m-%dT%H:%M:00")
        times['time_range'] = (times['start'], times['end'])
        times['rop_interval'] = self.ROP_INTERVAL

        log.logger.debug("Current timestamp: {0} ({1}), ROP to be Fetched: {2}-{3}"
                         .format(current_timestamp_secs, current_local_time, start_timestamp, end_timestamp))

        self.check_profile_memory_usage()
        return times

    def calculate_dst_offset_for_fetched_rop(self, current_timestamp_secs):
        """
        Calculate the offset to be applied to ROP start time based on whether DST is active or not for current time.

        :param current_timestamp_secs: Number of seconds since Epoch (Jan 1st 1970)
        :type current_timestamp_secs: float
        :return: Number of minutes to offset the start time of the ROP
        :rtype: int
        """
        start_time_dst_offset = 0

        if time.daylight:
            offset_local_dst_timezone_secs = time.altzone
            offset_local_non_dst_timezone_secs = time.timezone
            dst_offset_secs = offset_local_dst_timezone_secs - offset_local_non_dst_timezone_secs

            dst_enabled_for_current_timestamp = time.localtime(current_timestamp_secs).tm_isdst
            dst_enabled_for_start_time_of_fetched_rop = time.localtime(
                current_timestamp_secs - self.FETCH_ROP_AGE_NUMBER * self.ROP_INTERVAL * 60).tm_isdst

            if dst_enabled_for_current_timestamp and not dst_enabled_for_start_time_of_fetched_rop:
                start_time_dst_offset -= dst_offset_secs / 60

            if not dst_enabled_for_current_timestamp and dst_enabled_for_start_time_of_fetched_rop:
                start_time_dst_offset += dst_offset_secs / 60

            log.logger.debug("DST info:- dst_enabled_for_current_timestamp: {0}, "
                             "dst_enabled_for_start_time_of_fetched_rop: {1}, start_time_dst_offset: {2}"
                             .format(dst_enabled_for_current_timestamp, dst_enabled_for_start_time_of_fetched_rop,
                                     start_time_dst_offset))

        return start_time_dst_offset

    @staticmethod
    def are_ssh_credentials_valid(host, user, password=None, ssh_identity_file=None, ms_proxy=False,
                                  allow_agent=True, look_for_keys=True):
        """
        Checks whether the specified username and password are valid

        :param host: str, Hostname or IP address of the host to check
        :type host: str
        :param user: str, SSH username used to log in
        :type user: str
        :param password: str, SSH password used to log in
        :type password: str
        :param ssh_identity_file: str, the filename of a private key to try for authentication
        :type ssh_identity_file: str
        :param ms_proxy: bool, True to create an open socket or socket-like object (such as a `.Channel`)
                         to use for communication to the target host else False
        :type ms_proxy: bool
        :param allow_agent: bool, set to False to disable connecting to the SSH agent
        :type allow_agent: bool
        :param look_for_keys: bool, set to False to disable searching for discoverable private key files in ``~/.ssh/``
        :type look_for_keys: bool
        :return: bool, True if credentials are valid else False
        :rtype: bool
        """

        result = False
        log.logger.debug("Checking if SSH credentials are valid with host {0}".format(host))
        try:
            connection_mgr = shell.ConnectionPoolManager()
            connection = connection_mgr.get_connection(host, user, password, ssh_identity_file=ssh_identity_file,
                                                       ms_proxy=ms_proxy, allow_agent=allow_agent,
                                                       look_for_keys=look_for_keys)
            result = True
            log.logger.debug("Closing connection")
            connection_mgr.return_connection(host, connection)
            log.logger.debug("Established valid SSH credentials for {username}@{hostname}"
                             .format(username=user, hostname=host))
        except Exception as e:
            log.logger.debug("Exception in are_ssh_credentials_valid: {0}".format(str(e)))

        return result

    def execute_flow(self):
        """
        Main flow for PM_45, PM_26 and PM_28
        """
        self.state = 'RUNNING'
        self.is_physical = cache.is_host_physical_deployment()
        self.lms_host = cache.get_ms_host()
        self.is_cloud_native = cache.is_enm_on_cloud_native()
        try:
            self.updated_available_data_types = get_matched_supported_datatypes_with_configured_datatypes(self)
            self.data_type_file_id_dict = {data_type: [0, None] for data_type in self.updated_available_data_types}
            fls_tuple_list = self.initiate_profile_and_environment()
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            while self.keep_running():
                self.sleep_until_time()
                self.check_and_add_new_datatypes_to_datatype_fileid_dict()
                self.perform_fls_nbi_operations(fls_tuple_list)

    def perform_fls_nbi_operations(self, fls_tuple_list):
        """
        This method fetches the active scripting services ip's, enables password less login for profile user
        and performs the sftp transfer tasks
        :param fls_tuple_list: list of tuples containing enmutils_int.lib.pm_nbi.Fls object and sleep time
        :type fls_tuple_list: list
        :raises EnvironError: if password-less connection setup is not existed between LMS and Workload VM.
        """
        try:
            self.active_scripting_service_ip_list = self.get_active_scripting_service_ip_list()
            child = None
            if self.is_physical:
                log.logger.debug("LMS host IP address is :{0}".format(self.lms_host))
                try:
                    child = pexpect.spawn('ssh -o StrictHostKeyChecking=no root@{0}'.format(self.lms_host), timeout=30)
                    child.expect("root@")
                    log.logger.debug("Connected to LMS")
                except Exception:
                    raise EnvironError("The pexpect timed-out! Please check if there is password-less connection setup"
                                       "between LMS and Workload VM.")
            self.enable_passwordless_login_for_users(child, [fls.user for fls, _ in fls_tuple_list],
                                                     self.active_scripting_service_ip_list, is_scripting_vm=True)

            log.logger.debug("Not spawning any threads as there is only single user")
            perform_sftp_transfer_tasks(fls_tuple_list[0], self)
        except Exception as e:
            self.add_error_as_exception(e)

    def check_and_add_new_datatypes_to_datatype_fileid_dict(self):
        """
        Check and add new data types to data type file id dict, if any new data type is found at specific time.
        """
        now = datetime.datetime.now().strftime("%H:%M")
        log.logger.debug("Now time is {0} desired time is {1} to update the new data types in "
                         "data type file id dict.".format(now, self.DATA_TYPES_UPDATE_TIME))
        if now == self.DATA_TYPES_UPDATE_TIME:
            log.logger.debug("Check and add new data types to data type file id dict.")
            self.updated_available_data_types = get_matched_supported_datatypes_with_configured_datatypes(self)
            for data_type in self.updated_available_data_types:
                if data_type not in self.data_type_file_id_dict:
                    log.logger.debug("New data type '{0}' is added.".format(data_type))
                    self.data_type_file_id_dict[data_type] = [0, None]
            log.logger.debug("Data type file id dict, after new data types are "
                             "added: {0}".format(self.data_type_file_id_dict))


def get_files_to_collect(profile, fls):
    """
    Get the default PMIC file locations using the Fls.

    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :param fls: Fls object to create batch files.
    :type fls: enmutils_int.lib.pm_nbi.Fls

    :return: List of pmic filepath strings.
    :rtype: list
    """
    files = []
    timeout = 300
    start_time = time.time()
    for data_type, id_time_list in profile.data_type_file_id_dict.iteritems():
        log.logger.debug("Attempt to fetch the {0} files from FLS".format(data_type))
        if id_time_list[0]:
            order, limit, offset = None, None, None
            file_creation_time = id_time_list[1]
        else:
            order, limit, offset = "id desc", 1, "0"
            file_creation_time = 0

        try:
            data, last_file_id, last_file_creation_time = fls.get_pmic_rop_files_location(
                profile.NAME, data_type, file_id=id_time_list[0], file_creation_time=file_creation_time, orderby=order,
                limit=limit, offset=offset)
            profile.data_type_file_id_dict[data_type][0] = last_file_id if last_file_id else 0
            profile.data_type_file_id_dict[data_type][1] = last_file_creation_time if last_file_creation_time else ""
            files = files + data
        except Exception as e:
            profile.add_error_as_exception(e)
        end_time = time.time()

        if (end_time - start_time) >= timeout:
            log.logger.debug("Timeout occurred while querying FLS")
            profile.add_error_as_exception(
                TimeOutError("Could not complete FLS query for all datatypes, since 5 min timeout occurred"))
            break

    log.logger.debug("Number of files fetched from FLS: {0}".format(len(files)))
    log.logger.debug("Fetching files from FLS is complete")
    return files, profile.data_type_file_id_dict


def create_and_execute_sftp_threads(profile, fls, collection_times):
    """
    Execute threads and process the result.

    :param profile: PM_26 Profile object
    :type profile: Pm26Profile
    :param fls: Fls object to create batch files.
    :type fls: enmutils_int.lib.pm_nbi.Fls
    :param collection_times: Dictionary of times related to the iteration
    :type collection_times: dict
    :return: True (successful execution) if no exceptions occurred, otherwise False
    :rtype: bool
    """
    log.logger.debug("Create and execute threads")
    iteration_success = False
    sftp_batch_sets = []
    batch_name_prefix = profile.PM_NBI_SFTP_BATCH_FILENAME.format(username=fls.user.username)

    if profile.active_scripting_service_ip_list:

        for num in xrange(profile.N_SFTP_THREADS):
            scripting_service_ip = (profile.active_scripting_service_ip_list[num % len(profile.active_scripting_service_ip_list)])

            batch_filename = batch_name_prefix + "{:02d}".format(num)

            sftp_batch_sets.append((sftp_nbi_files,
                                    batch_filename,
                                    scripting_service_ip, fls.user.username))

        sftp_batch_sets.append((monitor_sftp_file_transfer, collection_times, fls.user.username, ""))

        tq = ThreadQueue(sftp_batch_sets, num_workers=len(sftp_batch_sets), func_ref=tq_task_executor,
                         args=[profile],
                         task_join_timeout=60,
                         task_wait_timeout=profile.time_remaining_for_sftp)
        tq.execute()

        log.logger.debug("Performing garbage collection ")
        collect()
        profile.check_profile_memory_usage()
        if tq.exceptions:
            log.logger.debug("Errors occurred during thread execution")
            profile.check_profile_memory_usage()
        else:
            log.logger.debug("Sftp thread execution complete without exceptions")
            iteration_success = True
        profile.log_results_of_nbi_transfer(iteration_success, collection_times, fls.user.username)
    else:
        log.logger.debug("No Scripting Service IP's available to connect to therefore the profile cannot launch "
                         "threads in order to sftp PM files from ENM to the Workload VM")
    profile.check_profile_memory_usage()
    return iteration_success
