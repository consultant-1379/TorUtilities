import time
import os
import datetime
import syslog
from functools import partial
import requests
from enmutils.lib import log, shell, filesystem, cache
from enmutils.lib.cache import get_apache_url, get_enm_cloud_native_namespace
from enmutils.lib.exceptions import EnvironError, TimeOutError
from enmutils.lib.shell import Command, run_local_cmd
from enmutils.lib.kubectl_commands import CHECK_SERVICES_CMD_ON_CN, CREATE_POD_ON_CN, DELETE_STATEFULSET_POD_ON_CN
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow, get_matched_supported_datatypes_with_configured_datatypes
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm, update_pib_parameter_on_enm

YAML_ZIP_FILE = get_internal_file_path_for_import("etc", "data", "yamls.zip")
FAN_CLIENT_YAML_FILE_PATH = get_internal_file_path_for_import("etc", "data/yamls", "fan_profile_pod_config.yaml")
FILE_ACCESS_NBI_URL = "/file/v1/files"
LOGIN_TO_ENM_CURL_CMD = "curl -k -L -c /var/tmp/cookie.txt -X POST {0}/login -d IDToken1={1} -d IDToken2={2}"
DOWNLOAD_CMD = "curl -s -S -k -X GET --cookie /var/tmp/cookie.txt --parallel --parallel-max {0} -K {1}"
FILES_DOWNLOAD_LOCATION = "/dev/null"
FAN_FOLDER = "/home/enmutils/fan/"
FAN_PROFILE_POD_YAML_FILE_NAME = "{0}.yaml"
JSON_HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}


class FileAccessNbiProfile(GenericFlow):
    FETCH_ROP_AGE_NUMBER = 1  # ROP being fetched is X number of ROP's ago from current ROP
    FAN_NBI_DIR = "/dev/shm/fan_nbi/{username}"  # Using tmpfs (/dev/shm) for faster storage on local system

    FAN_NBI_BATCH_FILES_DIR = "{0}/batch_files".format(FAN_NBI_DIR)
    FAN_NBI_BATCH_FILENAME = "{0}/pm_nbi_batch_".format(FAN_NBI_BATCH_FILES_DIR)
    FAN_PIDS_FILE = "{0}/pm_nbi_pids".format(FAN_NBI_BATCH_FILES_DIR)
    REMOVE_NBI_USER_DIR = 'rm -rf %s' % FAN_NBI_DIR
    # bash cmd set
    KILL_RUNNING_KUBECTL_COMMANDS_PROCESSES = 'cat %s|while read pid; do kill $pid; done'
    CHECK_FOR_RUNNING_FAN_CURL_PROCESSES = ('cat %s | while read pid; do ps -p $pid > /dev/null 2>&1; echo -n "$? "; done' % FAN_PIDS_FILE)
    DATA_TYPES = []

    def __init__(self):
        """
        Init Method
        """
        super(FileAccessNbiProfile, self).__init__()

        self.users = []
        self.data_type_file_id_dict = {}
        self.fan_pod_ip = None
        self.nbi_transfer_stats = dict()
        self.enm_url = None
        self.rest_api_main_url = None
        self.is_cloud_native = None
        self.count = 0
        self.updated_available_data_types = {}

    def execute_flow(self):
        """
        Main flow for FAN profiles

        """
        self.state = 'RUNNING'
        self.enm_url = get_apache_url()  # Get ENM GUI URL and set to variable
        self.rest_api_main_url = "https://{0}/{1}".format(self.enm_url.replace('https://', ''),
                                                          self.SERVICE_FORWARD_PORT)
        cenm_namespace = get_enm_cloud_native_namespace()
        self.is_cloud_native = cache.is_enm_on_cloud_native()
        pod_name = self.NAME.lower().replace("_", "-")
        try:
            self.users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
            self.updated_available_data_types = get_matched_supported_datatypes_with_configured_datatypes(self)
            self.data_type_file_id_dict = {user.username: {data_type: [0, None] for data_type in
                                                           self.updated_available_data_types} for user in self.users}

            if check_fileaccessnbi_is_running(cenm_namespace):
                pod_yaml_file_path = self.create_fan_pod_yaml_config_file_for_fan()
                self.teardown_list.append(partial(filesystem.delete_file, pod_yaml_file_path))
                if create_pod_on_cn(cenm_namespace, pod_yaml_file_path, pod_name):
                    self.teardown_list.append(partial(delete_pod_on_cn, cenm_namespace, pod_name))
                    self.fan_pod_ip = check_pod_is_running(cenm_namespace, pod_name=pod_name)
                    self.check_fan_nbi_directory(self.users[0].username)
                    self.teardown_list.append(partial(safe_teardown, self.KILL_RUNNING_KUBECTL_COMMANDS_PROCESSES.
                                                      format(username=self.users[0].username),
                                                      self.FAN_PIDS_FILE.format(username=self.users[0].username)))
                    self.teardown_list.append(partial(clear_fan_nbi_dir, self))
                    while self.keep_running():
                        self.sleep_until_time()
                        self.check_and_add_new_datatypes_to_datatype_fileid_dict()
                        if self.NAME == 'FAN_12':
                            self.enable_eniq_pib_parameters()
                        self.perform_file_access_nbi_operations(self.fan_pod_ip)
        except Exception as e:
            self.add_error_as_exception(e)

    def enable_eniq_pib_parameters(self):
        if self.count == 0:
            self.count += 1
            set_pib_parameters("true")
        check_pib_parameters_enabled(self)

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
                if data_type not in self.data_type_file_id_dict[self.users[0].username]:
                    log.logger.debug("New data type '{0}' is added.".format(data_type))
                    self.data_type_file_id_dict[self.users[0].username][data_type] = [0, None]
            log.logger.debug("Data type file id dict, after new data types are "
                             "added: {0}".format(self.data_type_file_id_dict))

    def perform_file_access_nbi_operations(self, pod_name):
        """
        Perform the file acccess nbi operations. i.e; Login to ENM from pod,
        Download the files in pod.

        :param pod_name: name of pod.
        :type pod_name: str
        :raises EnvironError: When Issue occurred while downloading the file.
        """
        username = self.users[0].username
        self.clear_fan_pid_file(username)
        collection_times = self.set_collection_times()
        try:
            user_data = {"enm_url": self.enm_url, "username": username, "password": self.users[0].password,
                         "datatypes": self.data_type_file_id_dict[username], "profilename": self.NAME,
                         "num_of_batches": self.NUM_OF_BATCHES}
            api = "{0}/fetchfiles".format(self.rest_api_main_url)
            log.logger.debug("Attempting to fetching the files locations using {0} Rest Api".format(api))
            log.logger.debug("fetchfiles payload: {0}".format(user_data))

            response = requests.post(api, json=user_data, headers=JSON_HEADERS, timeout=420, verify=False)
            log.logger.debug("Response of fetch files: {0} and status code: {1}".format(response.json(),
                                                                                        response.status_code))
            if response.status_code != 200 or response.json()['status'] is False:
                self.add_error_as_exception(EnvironError("{0} occurred while fetching files locations and code: {1}".format(response.json()['message'],
                                                                                                                            response.status_code)))
            if not response.json()['files'] or not response.json()['file_locations']:
                failure_reason = ("FLS has reported that no files exists for this ROP "
                                  "- see profile log for details of FLS queries performed")
                raise EnvironError("{0}".format(failure_reason))

            log.logger.debug("Successfully fetched files locations: {0}".format(response.json()))
            self.data_type_file_id_dict[username] = response.json()['data_types_dict']
            file_locations_in_pod = response.json()['file_locations']
            self.nbi_transfer_stats[username]["nbi_fls_file_count"] = response.json()['files']
            curl_end_time = (15 * 60) - (float(response.json()['total_time'].split(' ')[0]) * 60) - 20
            start_time_of_thread = time.time()
            log.logger.debug("Rop files downloading tasks - Started")
            iteration_success = download_multiple_batch_files_to_pod_with_api(file_locations_in_pod, pod_name, curl_end_time, self)
            log.logger.debug("Rop files downloading operation completed")

            self.nbi_transfer_stats[username]["nbi_transfer_time"] = time.time() - start_time_of_thread
            self.log_results_of_nbi_transfer(iteration_success, collection_times)
            self.check_profile_memory_usage()
        except Exception as e:
            self.add_error_as_exception(e)

    def log_results_of_nbi_transfer(self, iteration_success, collection_times):
        """
        Log the results of the fan files downloading operation
        Logging is happening to daemon logs, via separate lines per instrumentation value,
        and to syslog (i.e. /var/log/messages file), via 1 line with all results in 1 line.

        :param collection_times: Dictionary containing times related to the NBI fetch
        :type collection_times: dict

        :param iteration_success: Bool stating download files successful or not
        :type iteration_success: Bool
        """
        username = self.users[0].username
        missed_files_count = 0

        results_identifier_text = "NBI File Transfer Results for user {0}:".format(username)
        started_at_time = datetime.datetime.fromtimestamp(collection_times['start_time_of_iteration'])
        start_time = collection_times['start']
        end_time = collection_times['end']

        transfer_started_at_time_text = "STARTED_AT: {}".format(started_at_time)
        collected_rop_text = "COLLECTED_ROP: {0} -> {1}".format(start_time, end_time)

        nbi_transfer_stats = self.nbi_transfer_stats[username]

        if not iteration_success:
            for _, batch_file_count in nbi_transfer_stats['missed_file_count'].iteritems():
                missed_files_count += batch_file_count
            if not missed_files_count:
                missed_files_count = nbi_transfer_stats["nbi_fls_file_count"]

        fls_file_count_text = "FLS_FILE_COUNT: {0}".format(nbi_transfer_stats["nbi_fls_file_count"])
        transfer_file_count_text = ("TRANSFERRED_FILE_COUNT: {0}"
                                    .format(nbi_transfer_stats["nbi_fls_file_count"] - missed_files_count))
        missed_file_count_text = "MISSED_FILE_COUNT: {0}".format(missed_files_count)
        file_count_text = "{0}, {1}, {2}".format(fls_file_count_text, transfer_file_count_text,
                                                 missed_file_count_text)
        transfer_time_taken_text = ("TIME_TAKEN: {0:4.2f} min"
                                    .format(float(nbi_transfer_stats["nbi_transfer_time"]) / 60))

        extra_text = ""
        if missed_files_count:
            extra_text = "Note: Failures occurred - Check profile log for more details, "
            iteration_success = False

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

    def set_collection_times(self):
        """
        Define the range timestamps of current iteration.

        The start & end times are being calculated to correspond with actual ROP times and to ensure that all files that
        are expected to be stored on ENM, are done so well in advance of the NBI fan files fetch time.

        :return: times: Contains the start time, end time (for output) and range (for Fls query)
        :rtype: dict
        """
        log.logger.debug("1. Calculating ROP times to be used for performing FLS queries")
        self.nbi_transfer_stats[self.users[0].username] = {"nbi_transfer_time": 0, "nbi_fls_file_count": 0,
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

    def create_fan_pod_yaml_config_file_for_fan(self):
        """
        Creates directory to copy fan_client.yaml file, edit .yaml file contents with new pod name, pod cpu, pod memory
        :return: file path of pod config yaml file
        :rtype: str
        """
        profile_name = self.NAME.lower()
        file_path = os.path.join(FAN_FOLDER, FAN_PROFILE_POD_YAML_FILE_NAME.format(profile_name))
        log.logger.debug("Creating fan directory and {0} yaml pod config file".format(file_path))
        run_local_cmd(shell.Command('unzip {0} -d /opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils_int/etc/data/'.format(YAML_ZIP_FILE)))
        if not filesystem.does_dir_exist(FAN_FOLDER):
            filesystem.create_dir(FAN_FOLDER)
        with open(FAN_CLIENT_YAML_FILE_PATH, 'r') as f:
            lines = f.readlines()
        with open(file_path, 'w+') as f:
            for line in lines:
                if "podname" in line:
                    line = line.replace('podname', profile_name.replace("_", "-"))
                if "podcpu" in line:
                    line = line.replace('podcpu', self.POD_CPU)
                if "podmemory" in line:
                    line = line.replace('podmemory', self.POD_MEMORY)
                if "enmurl" in line:
                    line = line.replace('enmurl', self.enm_url.replace('https://', ''))
                f.write(line)
            log.logger.debug("FAN directory and {0} pod config file have been created".format(file_path))
        return file_path

    def check_fan_nbi_directory(self, username):
        """
        Check whether the FAN NBI directory exists; create it if missing.

        :param username: UserName
        :type username: str
        """
        pm_directory = self.FAN_NBI_BATCH_FILES_DIR.format(username=username)
        log.logger.debug("Checking to see if PM NBI directories exist on Workload VM: {0}".format(pm_directory))
        if not filesystem.does_dir_exist(pm_directory):
            log.logger.debug("Creating directory as it does not exist: {0}".format(pm_directory))
            shell.run_local_cmd(shell.Command('mkdir -p {0}'.format(pm_directory)))

        log.logger.debug("FAN NBI Directory checks completed")
        self.check_profile_memory_usage()

    def clear_fan_pid_file(self, username):
        """
        Clear the file containing fan curl pids

        :param username: UserName
        :type username: str
        """
        fan_file_path = self.FAN_PIDS_FILE.format(username=username)
        if filesystem.does_file_exist(fan_file_path):
            shell.run_local_cmd(shell.Command(r">{0}".format(fan_file_path)))


def download_multiple_batch_files_to_pod_with_api(batch_files, pod_name, curl_end_time, profile):
    """
    Download multiple batch files (rop files) to pod from fileaccessnbi service by calling rest api

    :param batch_files: list of rop file locations
    :type batch_files: list
    :param profile: FAN_01 Profile object
    :type profile: FAN_01Profile
    :param pod_name: name of pod.
    :type pod_name: str
    :param curl_end_time: time to kill curl process.
    :type curl_end_time:
    :return: True if iteration is success.
    :rtype: bool

    :raises EnvironError: When Issue occurred while downloading the file.
    """
    iteration_success = None
    api = "{0}/downloadfiles".format(profile.rest_api_main_url)
    log.logger.debug("Attempt to download the {0} batch files from "
                     "fileaccessnbi service to {1} pod using {2} Rest Api".format(batch_files, pod_name, api))
    try:
        payload = {"files_path": batch_files, "threads_count": profile.NUM_OF_CURL_PARALLEL_REQUESTS, "curl_end_time": curl_end_time}

        log.logger.debug("Download files payload : {0}".format(payload))
        response = requests.post(api, json=payload, headers=JSON_HEADERS, verify=False)
        log.logger.debug("Response of download files: {0} and status code: {1}".format(response.json(),
                                                                                       response.status_code))
        if response.status_code != 200:
            raise EnvironError("{0} occurred while downloading the {1} files from fileaccessnbi service".format(
                response.json(), batch_files))
        log.logger.debug("Successfully downloaded files: {0} on pod: {1}".format(batch_files, response.json()))
        iteration_success = response.json()['status']
    except Exception as e:
        profile.add_error_as_exception(e)
    profile.check_profile_memory_usage()

    return iteration_success


def check_fileaccessnbi_is_running(cenm_namespace):
    """
    checks whether fileaccessnbi service is running or not. it returns True, when fileaccessnbi service is running.

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :return: True if fileaccessnbi service is running.
    :rtype: bool

    :raises EnvironError: if fileaccessnbi service not running or not installed.
    """
    log.logger.debug("Attempt to check the fileaccessnbi service running status on Cloud native.")
    cmd = Command(CHECK_SERVICES_CMD_ON_CN.format(cenm_namespace, "fileaccessnbi"))
    response = run_local_cmd(cmd)
    if not response.ok:
        raise EnvironError("Issue occurred while checking the fileaccessnbi on Cloud native, Please check logs.")
    return True


def check_pod_is_running(cenm_namespace, pod_name, exp_time_in_min=2, sleep_time=20):
    """
    Wait and checks for pod to become 'Running'

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :param pod_name: name of pod.
    :type pod_name: str
    :param exp_time_in_min: expire time to check the running status of fan01 pod.
    :type exp_time_in_min: int
    :param sleep_time: sleep time for check the running status of fan01 pod.
    :type sleep_time: int

    :return: pod_name when pod is running.
    :rtype: str

    :raises TimeOutError: when pod status cannot be verified within given time (2 mins)

    """
    log.logger.debug("Attempt to check the {0} pod running status on Cloud native.".format(pod_name))
    expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=exp_time_in_min)
    while datetime.datetime.now() < expiry_time:
        cmd = Command(CHECK_SERVICES_CMD_ON_CN.format(cenm_namespace, pod_name))
        response = run_local_cmd(cmd)
        if response and "Running" in str(response.stdout):
            pod_name = response.stdout.split(" ")[0]
            log.logger.debug("{0} pod is in running state".format(pod_name))
            return pod_name
        log.logger.debug("Still, {0} pod not in running state, "
                         "Sleeping for {1} seconds before re-trying..".format(pod_name, sleep_time))
        time.sleep(sleep_time)

    raise TimeOutError("Issue occurred while checking {0} on Cloud native, Please check logs.".format(pod_name))


def delete_pod_on_cn(cenm_namespace, pod_name):
    """
    Deletes the specific pod on cenm.

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :param pod_name: name of pod.
    :type pod_name: str

    :return: True if pod deletion was success.
    :rtype: bool

    :raises EnvironError: if pod deletion is failed on cenm.
    """
    log.logger.debug("Attempt to delete the {0} pod".format(pod_name))
    cmd = shell.Command(DELETE_STATEFULSET_POD_ON_CN.format(pod_name, cenm_namespace))
    response = shell.run_local_cmd(cmd)
    if not response.ok:
        raise EnvironError("Issue occurred while Deleting the {0} pod on Cloud native, "
                           "Please check logs. {1}".format(pod_name, response.stdout))
    log.logger.debug("Successfully deleted {0} pod on Cloud native: {1}".format(pod_name, response.stdout))

    return True


def create_pod_on_cn(cenm_namespace, yaml_file_path, pod_name):
    """
    Creates pod on cENM server using yml file

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :param pod_name: name of pod
    :type pod_name: str
    :param yaml_file_path: poc creation configuration file path.
    :type yaml_file_path: str

    :return: True if  pod creation was success.
    :rtype: bool

    :raises EnvironError: if pod creation is failed.
    """
    log.logger.debug("Attempt to create {0} pod".format(pod_name))
    cmd = shell.Command(CREATE_POD_ON_CN.format(yaml_file_path, cenm_namespace))
    response = shell.run_local_cmd(cmd)
    if not response.ok:
        raise EnvironError("Issue occurred while creating the {0} pod on Cloud native, "
                           "Please check logs. {1}".format(pod_name, response.stdout))

    log.logger.debug("Successfully created {0} pod on Cloud native: {1}".format(pod_name, response.stdout))

    return True


def clear_fan_nbi_dir(profile):
    """
    Deletes the FAN_NBI_DIR on workload vm.

    :param profile: FAN Profile object
    :type profile: FANProfile
    """
    clear_nbi_dir = profile.REMOVE_NBI_USER_DIR.format(username=profile.users[0].username)
    shell.run_local_cmd(shell.Command(clear_nbi_dir))


def safe_teardown(kill_running_kubectl_commands_processes, fan_pids_file):
    """
    FAN_01 teardown method which will kill the running fan curl threads.

    :param kill_running_kubectl_commands_processes: Cmd to kill the running fan curl processes
    :type kill_running_kubectl_commands_processes: str
    :param fan_pids_file: Running fan curl pids
    :type fan_pids_file: str

    """
    shell.run_local_cmd(shell.Command(kill_running_kubectl_commands_processes % fan_pids_file, allow_retries=False))
    shell.run_local_cmd(shell.Command('>%s' % fan_pids_file, allow_retries=False))


def set_pib_parameters(value):
    """
    Set pib parameter values for ENIQ Stats Export
    :param value: Value to use when setting the PIB parameter value
    :type value: str
    """
    log.logger.debug("Setting PIB parameters for Topology Export")
    pib_parameters = ["topologyExportCreationEnabledStats", "topologyExportCreationEnabled",
                      "ETS_InventoryMoExportEnabled"]
    for pib_parameter in pib_parameters:
        state = get_pib_value_on_enm(enm_service_name='impexpserv',
                                     pib_parameter_name=pib_parameter,
                                     service_identifier="eniq-topology-service-impl" if 'topology' in pib_parameter
                                     else "")
        if str(state).lower() == 'false':
            log.logger.debug("pib parameters are not set, so enabling the pib parameters")
            update_pib_parameter_on_enm(enm_service_name='impexpserv',
                                        pib_parameter_name=pib_parameter,
                                        pib_parameter_value=value,
                                        service_identifier="eniq-topology-service-impl" if 'topology' in pib_parameter
                                        else "")

    log.logger.debug("Setting PIB parameters complete")


def check_pib_parameters_enabled(profile):
    """
    :param profile: FAN Profile object
    :type profile: FANProfile
    """
    now = datetime.datetime.now().strftime("%H:%M")
    log.logger.debug("now time is {0} desired time is {1}".format(now, profile.DESIRED_TIME))
    if now == profile.DESIRED_TIME:
        set_pib_parameters("true")
