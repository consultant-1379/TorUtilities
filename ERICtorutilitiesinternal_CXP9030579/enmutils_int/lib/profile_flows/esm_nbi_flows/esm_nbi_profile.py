import time
import datetime
from functools import partial
import syslog
import yaml
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib import log, shell
from enmutils.lib.cache import get_apache_url, get_enm_cloud_native_namespace
from enmutils.lib.exceptions import EnvironError, TimeOutError
from enmutils.lib.shell import Command, run_local_cmd
from enmutils.lib.kubectl_commands import CHECK_CONFIGMAP_CMD_ON_CN, CREATE_POD_ON_CN, DELETE_K8S_OBJECTS, \
    CHECK_SERVICES_CMD_ON_CN
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from kubernetes import client, config

ESM_CLIENT_YAML_FILE_PATH = get_internal_file_path_for_import("etc", "data/yamls", "esm_nbi_client.yaml")
YAML_ZIP_FILE = get_internal_file_path_for_import("etc", "data", "yamls.zip")


class EsmNbiProfile(GenericFlow):
    FETCH_ROP_AGE_NUMBER = 1  # ROP being fetched is X number of ROP's ago from current ROP
    NEW_REMOTE_WRITE_URL = "http://remotewriter-nbi-profile:1234/receive"
    READ_TIMEOUT = "30s"
    NEW_REMOTE_WRITE_NAME = "esm_nbi_01"
    PROMETHEUS_FILE_NAME = "prometheus.yml"
    PROM_TOOL_QUERY = '''/usr/local/bin/kubectl --kubeconfig /root/.kube/config exec -n namespace eric-pm-server-0 -c eric-pm-server -- bash -c "promtool query range http://localhost:9090 'sum(rate(prometheus_remote_storage_samples_retried_total{url=\\"remote_write_url\\"}[5m])) by (remote_name)' --start=$(($(date +%s) - 900)) --end=$(date +%s) --step=60s"'''

    def __init__(self):
        """
        Init Method
        """
        super(EsmNbiProfile, self).__init__()

        self.enm_url = None
        self.users = []
        self.cenm_namespace = None
        self.configmap_name = 'eric-pm-server'
        self.pod_name = 'remotewriter-nbi-profile'
        self.nbi_transfer_stats = dict()

    def execute_flow(self):
        """
        Main flow for ESM_NBI profiles
        """
        self.state = 'RUNNING'
        self.enm_url = get_apache_url()
        self.cenm_namespace = get_enm_cloud_native_namespace()
        try:
            self.users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
            if check_configmap_exists_on_cn(self.cenm_namespace):
                self.perform_prerequisites()
                while self.keep_running():
                    self.sleep_until_time()
                    self.perform_esm_nbi_operations()

        except Exception as e:
            self.add_error_as_exception(e)

    def perform_prerequisites(self):
        """
        This method performs following operations. i.e.; create pod on cn and updates config map with new
        remote_write url

        """
        run_local_cmd(shell.Command('unzip {0} -d /opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils_int/etc/data/'.format(YAML_ZIP_FILE)))
        if create_pod_on_cn(self.cenm_namespace, ESM_CLIENT_YAML_FILE_PATH, self.pod_name):
            self.teardown_list.append(
                partial(delete_pod_on_cn, self.cenm_namespace, ESM_CLIENT_YAML_FILE_PATH, self.pod_name))
            if check_pod_is_running(self.cenm_namespace, pod_name=self.pod_name):
                self.update_remote_write_url_in_configmap(self.cenm_namespace, self.configmap_name,
                                                          action='add')
                self.teardown_list.append(
                    partial(picklable_boundmethod(self.update_remote_write_url_in_configmap),
                            self.cenm_namespace, self.configmap_name,
                            action='remove'))

    def perform_esm_nbi_operations(self):
        """
        Perform the esm nbi operations. i.e; create remote_writer_pod, update service url in configmap &
        receive metrics from prometheus, Login to ENM from pod,

        """
        try:
            collection_times = self.set_collection_times()
            if self.verify_remote_write_url_in_configmap(self.cenm_namespace, self.configmap_name):
                self.verify_metrics_received_into_pod(self.cenm_namespace, self.NEW_REMOTE_WRITE_URL)
                self.log_results_of_nbi_metrics_received(collection_times)
            else:
                self.update_remote_write_url_in_configmap(self.cenm_namespace, self.configmap_name, action='add')
                self.verify_metrics_received_into_pod(self.cenm_namespace, self.NEW_REMOTE_WRITE_URL)
                self.log_results_of_nbi_metrics_received(collection_times)

        except Exception as e:
            self.add_error_as_exception(e)

    def verify_metrics_received_into_pod(self, cenm_namespace, remote_write_url):
        """
        verify metrics being received into pod

        :param cenm_namespace: namespace of cenm server.
        :type cenm_namespace: str
        :param remote_write_url: remote_write_url in cenm server.
        :type remote_write_url: str

        :raises EnvironError: When Issue occurred while downloading the file.
        """

        failed_timestamps = []
        username = self.users[0].username
        kubectl_cmd = self.PROM_TOOL_QUERY.replace("namespace", str(cenm_namespace)).replace("remote_write_url",
                                                                                             str(remote_write_url))
        log.logger.debug('promtool query is {0}'.format(kubectl_cmd))
        response = shell.run_local_cmd(kubectl_cmd)
        if not response.ok:
            raise EnvironError("Issue occurred while executing promtool query {0} in Cloud native inside pod, "
                               "Please check logs. {1}".format(kubectl_cmd, response.stdout))
        response = response.stdout.split('\n')[1:-1]
        for data in response:
            timestamp = data.split('@')[1].strip()
            data = data.split('@')[0].strip()
            if data != '0':
                timestamp = datetime.datetime.utcfromtimestamp(float(timestamp[1:-1])).strftime('%Y-%m-%d %H:%M:%S')
                failed_timestamps.append((data, timestamp))
        if failed_timestamps:
            self.nbi_transfer_stats[username]["failed_timestamps"] = failed_timestamps
            self.add_error_as_exception(
                EnvironError("Metrics are not received into pod, please check the eric-pm-server. \n "
                             "Note: Failures may be because of the application(eric-pm-server-0) downtime during "
                             "upgrade. Please check"))
            self.check_profile_memory_usage()

    def verify_remote_write_url_in_configmap(self, cenm_namespace, configmap_name):
        """

        update configmap with new remote_write url

        :param cenm_namespace: namespace of cenm server.
        :type cenm_namespace: str
        :param configmap_name: configmap_name in cenm server.
        :type configmap_name: str

        :return: True when remote_write url configured in configmap is running.
        :rtype: bool
        """
        new_remote_write_url = self.NEW_REMOTE_WRITE_URL
        _, configmap = self.get_prometheus_config(cenm_namespace, configmap_name)
        prometheus_yaml = configmap.data[self.PROMETHEUS_FILE_NAME]
        prometheus_config = yaml.safe_load(prometheus_yaml)
        for rw in prometheus_config['remote_write']:
            if rw['url'] == new_remote_write_url:
                return True
        return False

    def update_remote_write_url_in_configmap(self, cenm_namespace, configmap_name, action):
        """

        update configmap with new remote_write url

        :param cenm_namespace: namespace of cenm server.
        :type cenm_namespace: str
        :param configmap_name: configmap_name in cenm server.
        :type configmap_name: str
        :param action: add, remove remote_write_url
        :type action: str
        """
        new_remote_write_url = self.NEW_REMOTE_WRITE_URL
        read_timeout = self.READ_TIMEOUT
        new_name = self.NEW_REMOTE_WRITE_NAME

        api_client, configmap = self.get_prometheus_config(self.cenm_namespace, self.configmap_name)

        prometheus_yaml = configmap.data[self.PROMETHEUS_FILE_NAME]
        remote_write_index = None
        prometheus_lines = prometheus_yaml.split('\n')
        # Add the new remote write URL to the existing Prometheus configuration
        if action == 'add':
            for index, line in enumerate(prometheus_lines):
                if line.strip() == 'remote_write:':
                    remote_write_index = index
            if remote_write_index is not None:
                new_remote_write = '  - url: {0}\n    remote_timeout: {1}\n    name: {2}'.format(
                    new_remote_write_url, read_timeout, new_name)
                prometheus_lines.insert(remote_write_index + 1, new_remote_write)

        elif action == 'remove':
            log.logger.debug('Called remove configmap and url to be removed is {0}'.format(new_remote_write_url))
            for index, line in enumerate(prometheus_lines):
                if line.strip() == '- url: http://remotewriter-nbi-profile:1234/receive':
                    log.logger.debug('inside if')
                    remote_write_index = index

            # Append the new remote write URL to the Prometheus configuration
            prometheus_lines.pop(remote_write_index)
            prometheus_lines.pop(remote_write_index)
            prometheus_lines.pop(remote_write_index)

        # Update the Prometheus YAML in the ConfigMap data
        prometheus_yaml_updated = '\n'.join(prometheus_lines)
        configmap.data['prometheus.yml'] = prometheus_yaml_updated

        # Update the ConfigMap
        api_client.replace_namespaced_config_map(configmap_name, cenm_namespace, configmap)

        if action == 'add':
            log.logger.debug('configmap updated with new remote write url, sleeping for 15 mins for the changes to effect')
            time.sleep(15 * 60)

    def get_prometheus_config(self, cenm_namespace, configmap_name):
        """
        update configmap with new remote_write url

        :param cenm_namespace: namespace of cenm server.
        :type cenm_namespace: str
        :param configmap_name: configmap_name in cenm server.
        :type configmap_name: str

        :return: api_client when pod is running.
        :rtype: external client
        :return: configmap when pod is running.
        :rtype: configmap
        """

        # Load the Kubernetes configuration
        config.load_kube_config()

        # Create a Kubernetes API client
        api_client = client.CoreV1Api()

        configmap = api_client.read_namespaced_config_map(configmap_name, cenm_namespace)

        return api_client, configmap

    def log_results_of_nbi_metrics_received(self, collection_times):
        """
        Log the results of the esm nbi metrics received into pod
        Logging is happening to daemon logs, via separate lines per instrumentation value,
        and to syslog (i.e. /var/log/messages file), via 1 line with all results in 1 line.

        :param collection_times: Dictionary containing times related to the NBI fetch
        :type collection_times: dict
        """
        username = self.users[0].username

        results_identifier_text = "NBI Metrics received Results for user {0}:".format(username)
        started_at_time = datetime.datetime.fromtimestamp(collection_times['start_time_of_iteration'])
        start_time = collection_times['start']
        end_time = collection_times['end']

        transfer_started_at_time_text = "STARTED_AT: {0}".format(started_at_time)
        collected_rop_text = "COLLECTED_ROP: {0} -> {1}".format(start_time, end_time)

        nbi_transfer_stats = self.nbi_transfer_stats[username]
        extra_text = ''
        if nbi_transfer_stats['failed_timestamps'] == 0:
            iteration_success = True
        else:
            extra_text = "Note: Prometheus retried number of samples per second to NBI at their respective timestamps "
            iteration_success = False

        failed_timestamps = "FAILED_TIMESTAMPS: {0}".format(nbi_transfer_stats['failed_timestamps'])
        metric_count_text = "{0}".format(failed_timestamps)

        transfer_result_text = "{0}SUCCESS: {1}".format(extra_text, iteration_success)
        instrumentation_data = ("{0}, {1}, {2}, {3}"
                                .format(collected_rop_text, transfer_started_at_time_text,
                                        metric_count_text, transfer_result_text))

        info_to_be_logged = "{0} {1}- {2}".format(self.NAME, results_identifier_text, instrumentation_data)

        # Log results to profile daemon log
        log.logger.debug(info_to_be_logged)

        syslog.syslog(info_to_be_logged)

    def set_collection_times(self):
        """
        Define the range timestamps of current iteration.

        The start & end times are being calculated to correspond with actual ROP times and to ensure that all files that
        are expected to be stored on ENM, are done so well in advance of the NBI fan files fetch time.

        :return: times: Contains the start time, end time (for output) and range (for Fls query)
        :rtype: dict
        """
        log.logger.debug("Calculating ROP times to be used for performing FLS queries")
        self.nbi_transfer_stats[self.users[0].username] = {"failed_timestamps": 0}
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


def check_configmap_exists_on_cn(cenm_namespace):
    """
    checks whether eric-pm-server configmap exists or not. it returns True, when eric-pm-server configmap is present.


    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :return: True if eric-pm-server configmap is running.
    :rtype: bool

    :raises EnvironError: if eric-pm-server configmap not present.
    """

    log.logger.debug("Attempt to check the eric-pm-server configmap configured status on Cloud native.")
    cmd = Command(CHECK_CONFIGMAP_CMD_ON_CN.format(cenm_namespace, "eric-pm-server"))
    response = run_local_cmd(cmd)
    if not response.ok:
        raise EnvironError(
            "Issue occurred while checking the eric-pm-server configmap on Cloud native, Please check logs.")
    return True


def create_pod_on_cn(cenm_namespace, yaml_file_path, pod_name):
    """
    Creates pod on cENM server using yml file

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :param pod_name: name of pod
    :type pod_name: str
    :param yaml_file_path: pod creation configuration file path.
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


def delete_pod_on_cn(cenm_namespace, yaml_file_path, pod_name):
    """
    Deletes the specific k8s objects defined in yaml file on cenm.

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :param yaml_file_path: pod deletion configuration file path.
    :type yaml_file_path: str
    :param pod_name: name of pod
    :type pod_name: str

    :return: True if pod deletion was success.
    :rtype: bool

    :raises EnvironError: if pod deletion is failed on cenm.
    """
    log.logger.debug("Attempt to delete the {0} pod".format(pod_name))
    cmd = shell.Command(DELETE_K8S_OBJECTS.format(yaml_file_path, cenm_namespace))
    response = shell.run_local_cmd(cmd)
    if not response.ok:
        raise EnvironError("Issue occurred while Deleting the {0} k8s objects on Cloud native, "
                           "Please check logs. {1}".format(yaml_file_path, response.stdout))
    log.logger.debug("Successfully deleted {0} pod on Cloud native: {1}".format(pod_name, response.stdout))

    return True


def check_pod_is_running(cenm_namespace, pod_name, exp_time_in_min=2, sleep_time=20):
    """
    wait and checks for fan01 to become 'Running'

    :param cenm_namespace: namespace of cenm server.
    :type cenm_namespace: str
    :param pod_name: name of pod.
    :type pod_name: str
    :param exp_time_in_min: expire time to check the running status of fan01 pod.
    :type exp_time_in_min: int
    :param sleep_time: sleep time for check the running status of fan01 pod.
    :type sleep_time: int

    :return: True when pod is running.
    :rtype: bool

    :raises TimeOutError: when pod status cannot be verified within given time

    """
    log.logger.debug("Attempt to check the {0} pod running status on Cloud native.".format(pod_name))
    expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=exp_time_in_min)
    while datetime.datetime.now() < expiry_time:
        cmd = Command(CHECK_SERVICES_CMD_ON_CN.format(cenm_namespace, pod_name))
        response = run_local_cmd(cmd)
        if response and "Running" in str(response.stdout):
            return True
        log.logger.debug("Still, {0} pod not in running state, "
                         "Sleeping for {1} seconds before re-trying..".format(pod_name, sleep_time))
        time.sleep(sleep_time)

    raise TimeOutError("Issue occurred while checking {0} on Cloud native, Please check logs.".format(pod_name))
