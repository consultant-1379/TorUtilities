import json
import re
import syslog
import time
from datetime import datetime
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.shell import Command, run_local_cmd
from enmutils.lib.cache import get_enm_cloud_native_namespace
from enmutils.lib import log
from enmutils.lib.kubectl_commands import CHECK_SERVICES_CMD_ON_CN
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from dateutil.parser import parse
import pytz
from pytz import timezone


GET_POD_LOGS_CMD = ("/usr/local/bin/kubectl exec {0} -n {1} "
                    "-- sh -c \'if [ -f \"/log_filter/log_filter.py\" ]; then "
                    "python3 /log_filter/log_filter.py -n {2}; "
                    "else tail /var/log/all.log -n 10000 | shuf -n {2}; fi\'")
GET_POD_TIMEZONE = "/usr/local/bin/kubectl describe po opendj-0 -n {0} | grep TZ"
GET_SYSLOG_NAMESPACE_CMD = ("/usr/local/bin/kubectl --kubeconfig /root/.kube/config get namespace "
                            "2>/dev/null | egrep syslog")


class LtSysLogStreamFlow(GenericFlow):

    def __init__(self):
        """
        Init Method
        """
        super(LtSysLogStreamFlow, self).__init__()
        self.users = []
        self.cenm_external_namespace = "syslog"  # syslog is external cenm namespace
        self.cenm_namespace = None
        self.pod_name = None
        self.nbi_transfer_stats = dict()

    def check_if_syslog_namespace_exists(self):
        """
        Checks whether syslog namespace is existed or not in this cenm deployment.
        :raises EnvironError: syslog namepsace is nog existed on this deployment
        """
        response = run_local_cmd(GET_SYSLOG_NAMESPACE_CMD)
        if response.ok and self.cenm_external_namespace in str(response.stdout):
            log.logger.debug("Syslog namespace is existed on this deployment, "
                             "Response: {0}".format(response.stdout))
        else:
            raise EnvironError("Syslog namespace is not existed on this deployment, "
                               "Response: {0}".format(response.stdout))

    def execute_flow(self):
        """
        Main flow for LtSysLogStream 01 profile

        """
        self.state = 'RUNNING'
        try:
            self.check_if_syslog_namespace_exists()
            self.cenm_namespace = get_enm_cloud_native_namespace()
            self.users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
            self.pod_name = get_pod_info_in_cenm("eric-enm-syslog-receiver", self.cenm_external_namespace)
            while self.keep_running():
                self.sleep_until_time()
                self.lt_sys_log_stream_operations()
        except Exception as e:
            self.add_error_as_exception(e)

    def get_pod_timezone(self):
        """
        Get the timezone of the pod.
        :return: timezone of the pod
        :rtype: str

        :raises EnvironError: Unable to get opendj-0 pod timezone.
        """
        log.logger.debug("Attempt to get the opendj-0 pod timezone")

        cmd = Command(GET_POD_TIMEZONE.format(self.cenm_namespace))
        response = run_local_cmd(cmd)
        log.logger.debug("Response of get opendj-0 pod timezone command: {0}".format(response.stdout))
        if not response.ok:
            raise EnvironError("Unable to get opendj-0 pod timezone due to {0}".format(response.stdout))
        pod_timezone = re.search(r"TZ:\s*(\S+)", response.stdout).group(1)
        log.logger.debug("opendj-0 pod timezone: {0}".format(pod_timezone))
        self.check_profile_memory_usage()

        return pod_timezone

    def get_logs_from_syslog_pod(self):
        """
        Get streamed logs from sys log receiver pod.

        :raises EnvironError: Issue occurred while executing Get pod logs command, while fetching the logs
                              from syslog receiver.
        :return: log stream logs (syslogs)
        :rtype: str
        """
        log.logger.debug("Attempt to get the log from {0} pod".format(self.pod_name))
        # Exec into the syslog container and tail a number of logs from the log file
        cmd = GET_POD_LOGS_CMD.format(self.pod_name, self.cenm_external_namespace, self.NUM_OF_LOGS)
        log.logger.debug("Get pod logs command: {0}".format(cmd))
        response = run_local_cmd(cmd)

        self.check_profile_memory_usage()
        if not response.ok and "Error from server (NotFound)" not in response.stdout:
            raise EnvironError("Issue occurred while executing get pod logs command {0} while fetching the logs "
                               "from syslog receiver, Please check logs. {1}".format(cmd, response.stdout))
        return response.stdout.strip()

    def parse_results(self, syslogs):
        """
         Iterate through each JSON log, convert the SG timestamp to UTC and
         compare with the timestamp (timegenerated) at rsyslog end
        :param syslogs: log stream logs
        :type syslogs: str
        """
        application_timezone = timezone(self.get_pod_timezone())  # get timezone of opendj-0 pod timezone.
        self.nbi_transfer_stats = {"failed_timestamps": []}
        failed_timestamps = []
        syslogs_info = syslogs.splitlines()
        log.logger.debug("{0} logs are fetched from {1} pod".format(len(syslogs_info), self.pod_name))
        for line in syslogs_info:
            log_info = json.loads(line)
            iso_datetime = parse(log_info['timestamp'])  # convert string datetime to datetime
            # convert 2023-08-09T08:03:35.780+00:00 to 2023-08-09 08:03:35 datetime object
            timestamp = datetime.strptime(iso_datetime.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
            # convert timestamp value to opendj-0 pod timezone (eEurope/Dublin) time and
            # again it is converted to UTC timezone time
            adjusted_timestamp = application_timezone.localize(datetime(timestamp.year, timestamp.month,
                                                                        timestamp.day, timestamp.hour, timestamp.minute,
                                                                        timestamp.second,
                                                                        timestamp.microsecond)).astimezone(pytz.utc)
            # convert 2023-08-09T08:03:35.780+00:00 to 2023-08-09T08:03:35.780+00:00 datetime object
            timegenerated = parse(log_info['timegenerated'])
            time_diff = timegenerated - adjusted_timestamp
            total_seconds_diff = round(time_diff.total_seconds(), 2)
            #  Get current date time and set hour, minute, micrseconds to 0
            current_time_now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            # get minute value from below datetime
            time_diff_minutes = (current_time_now + time_diff).minute
            log_fail_status = self.verify_if_log_is_failed(total_seconds_diff, time_diff_minutes)
            if log_fail_status:
                failed_timestamps.append({"timegenerated": log_info['timegenerated'],
                                          "timestamp": str(adjusted_timestamp).replace(' ', 'T'),
                                          "hostname": log_info['hostname']})
        if failed_timestamps:
            self.nbi_transfer_stats["failed_timestamps"] = failed_timestamps
            trimmed_failed_timestamps = [{"timegenerated": timestamps["timegenerated"],
                                          "hostname": timestamps["hostname"]} for timestamps in failed_timestamps[:5]]
            self.add_error_as_exception(
                EnvironError("{0}....., {1} logs are not received to syslog receiver with in "
                             "1 minute. Please check logs".format(trimmed_failed_timestamps,
                                                                  len(failed_timestamps))))
        self.check_profile_memory_usage()

    def verify_metrics_received_into_pod(self):
        """
        Verify metrics being received into sys log receiver.
        """
        profile_start_timestamp_secs = int(time.time())
        log_stream_logs = self.get_logs_from_syslog_pod()
        self.parse_results(log_stream_logs)
        self.log_results_of_nbi_metrics_received(profile_start_timestamp_secs)

    def lt_sys_log_stream_operations(self):
        """
        Perform the lt sys log stream_operations. i.e.; verify logs are received in syslog receiver,
        whether the log was streamed to receiver within 1 minute
        """
        try:
            self.verify_metrics_received_into_pod()
        except Exception as e:
            self.add_error_as_exception(e)

    def log_results_of_nbi_metrics_received(self, profile_start_timestamp_secs):
        """
        Log the results of the log stream received into sys log receiver.
        Logging is happening to daemon logs, via separate lines per instrumentation value,
        and to syslog (i.e. /var/log/messages file), via 1 line with all results in 1 line.

        :param profile_start_timestamp_secs: unix time stamp of rofile start time
        :type profile_start_timestamp_secs: int
        """
        username = self.users[0].username

        results_identifier_text = "SYS Logs metrics received Results for user {0}:".format(username)
        started_at_time = datetime.fromtimestamp(profile_start_timestamp_secs)

        transfer_started_at_time_text = "PROFILE_START_TIME: {0}".format(started_at_time)

        nbi_transfer_stats = self.nbi_transfer_stats
        extra_text = ''
        if nbi_transfer_stats['failed_timestamps']:
            extra_text = "Note: Few logs are not received (streamed) to syslog receiver with in 1 minute, "
            iteration_success = "FAIL"
        else:
            iteration_success = "PASS"

        failed_timestamps = "FAILED_TIMESTAMPS: {0}".format(nbi_transfer_stats['failed_timestamps'])
        verified_logs_count = "VERIFIED_LOGS_COUNT: {0}".format(self.NUM_OF_LOGS)
        failed_logs_count = "FAILED_LOGS_COUNT: {0}".format(len(nbi_transfer_stats['failed_timestamps']))

        metric_count_text = "{0}, {1}, {2}".format(verified_logs_count, failed_logs_count, failed_timestamps)

        transfer_result_text = "{0}RESULT: {1}".format(extra_text, iteration_success)
        instrumentation_data = ("{0}, {1}, {2}"
                                .format(transfer_started_at_time_text,
                                        metric_count_text, transfer_result_text))

        info_to_be_logged = "{0} {1}- {2}".format(self.NAME, results_identifier_text, instrumentation_data)

        # Log results to profile daemon log
        log.logger.debug(info_to_be_logged)
        syslog.syslog(info_to_be_logged)

    def verify_if_log_is_failed(self, total_seconds_diff, time_diff_minutes):
        """
        Verify log timestamp, if it is received within 1 minute time.
        In cases where the timedelta is greater than 1 hour,
        the hour/multiples of hrs (e.g. 60/120/180 mins) should be subtracted
        from the timedelta to leave the actual time taken to stream the log
        e.g. initial timedelta of 1hr 5mins - 1hr = 5 mins (the resulting timedelta / the time taken to stream the log)

        :param total_seconds_diff: total seconds time difference between the timestamp and timegenerated.
        :type total_seconds_diff: float
        :param time_diff_minutes: time difference minute.
        :type time_diff_minutes: float

        :return: returns True, if log not received to sys log receiver within 1 minute.
        :rtype: bool
        """
        if 60 < total_seconds_diff < 3600:
            status = True
        elif total_seconds_diff > 3600 and round((time_diff_minutes * 60), 2) > 60:
            status = True
        else:
            status = False
        return status


def get_pod_info_in_cenm(service_name, enm_namespace):
    """
    Fetch Pod details (from Kubernetes cluster) for given service name

    :param service_name: ENM Service identifier, e.g. pmserv, fmserv etc
    :type service_name: str
    :param enm_namespace: namespace
    :type enm_namespace: str
    :return: service pod name
    :rtype: str

    :raises EnvironError: Syslog reciever pod is not found on this deployment or pod is not in running state.
    """
    pod_name = None
    log.logger.debug("Fetching service hostnames from Kubernetes client for service '{0}'".format(service_name))
    cmd = Command(CHECK_SERVICES_CMD_ON_CN.format(enm_namespace, service_name))
    response = run_local_cmd(cmd)
    if not response.ok and not response.stdout:
        raise EnvironError("{0} pod is not found on this deployment.".format(service_name))
    else:
        pod_name = response.stdout.split(" ")[0]
        if "Running" in str(response.stdout):
            log.logger.debug("{0} pod is in running state".format(pod_name))
        else:
            raise EnvironError("{0} pod is not running state".format(pod_name))
    return pod_name
