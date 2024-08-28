from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class FileAccessNbiProfile(PlaceHolderFlow):
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """

    def __init__(self):  # pylint: disable=unused-argument
        self.users = []
        self.data_type_file_id_dict = {}
        self.fan_pod_ip = None
        self.nbi_transfer_stats = dict()
        self.enm_url = None
        self.time_remaining_for_download = 0

    def execute_flow(self):  # pylint: disable=unused-argument
        pass

    def perform_file_access_nbi_operations(self, pod_name):  # pylint: disable=unused-argument
        pass

    def transfer_batch_files_to_pod(self):  # pylint: disable=unused-argument
        pass

    def log_into_enm_from_pod(self, pod_name):  # pylint: disable=unused-argument
        pass

    def log_results_of_nbi_transfer(self, collection_times):  # pylint: disable=unused-argument
        pass

    def set_collection_times(self):  # pylint: disable=unused-argument
        pass

    def calculate_dst_offset_for_fetched_rop(self, current_timestamp_secs):  # pylint: disable=unused-argument
        pass

    def get_list_of_files_from_fls(self, fls):  # pylint: disable=unused-argument
        pass

    def create_fan_pod_yaml_config_file_for_fan(self):  # pylint: disable=unused-argument
        pass

    def check_fan_nbi_directory(self, username):  # pylint: disable=unused-argument
        pass

    def create_batch_files_on_server(self, files_to_collect, shuffle_data=True):  # pylint: disable=unused-argument
        pass

    def clear_fan_pid_file(self, username):  # pylint: disable=unused-argument
        pass


def download_files_to_pod(batch_file_info, pod_name, profile):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def check_fileaccessnbi_is_running(cenm_namespace):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def check_pod_is_running(cenm_namespace, pod_name, exp_time_in_min=2, sleep_time=20):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def get_files_to_collect(profile, fls):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def delete_pod_on_cn(cenm_namespace, pod_name):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def create_pod_on_cn(cenm_namespace, yaml_file_path, pod_name):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def clear_fan_nbi_dir(profile):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def monitor_fan_files_download(collection_times, username, profile):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def check_that_fan_curl_processes_are_complete(profile, username, start_time_of_thread,
                                               fan_files_downloading_process_checking_interval,
                                               number_of_checks_to_perform, time_remaining_for_iteration):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def any_fan_curl_processes_still_running(checkpoint_indicator, profile, username, start_time_of_thread):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def safe_teardown(kill_running_kubectl_commands_processes, fan_pids_file):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass


def tq_task_executor(task_set, profile):  # pylint: disable=unused-argument
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    pass
