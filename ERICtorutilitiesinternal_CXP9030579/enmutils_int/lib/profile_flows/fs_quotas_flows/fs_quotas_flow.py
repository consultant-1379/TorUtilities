import time
import subprocess
import json
from datetime import datetime
import pexpect
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.cache import get_enm_cloud_native_namespace, is_enm_on_cloud_native
from enmutils.lib import log, shell
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow import get_pod_info_in_cenm
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_list_of_scripting_service_ips
from enmutils_int.lib.services.deployment_info_helper_methods import get_hostname_in_cloud_native


WRITE_QUOTA_CONFIG_URL = "/filesystem-quota-service/quotas-config/writeQuotaConfiguration"
READ_QUOTA_CONFIG_URL = "/filesystem-quota-service/quotas-config/readQuotaConfiguration"
DIT_URL = "https://atvdit.athtem.eei.ericsson.se"


class FsQuotas01Flow(GenericFlow):
    NUMBER_OF_RETRIES = 10
    SCRIPTING_SERVICE_PODS_PORTS = [5020, 5021]

    def __init__(self):
        """
        Init Method
        """
        super(FsQuotas01Flow, self).__init__()
        self.user = []
        self.cenm_namespace = None
        self.pod_name = None
        self.nbi_transfer_stats = dict()
        self.last_used_scripting_service_port = None
        self.scripting_service_ports_index = 0
        self.currently_used_scripting_service_port = 0
        self.iteration_success = False
        self.scripting_service_ip_list = None

    def execute_flow(self):
        """
        Main flow for FS QUOTAS 01 profile

        """
        self.state = 'RUNNING'

        try:
            if is_enm_on_cloud_native():
                if self.verify_whether_deployment_type_is_cnis():
                    self.cenm_namespace = get_enm_cloud_native_namespace()
                    self.user = self.create_custom_user_in_enm(user_string="Cephtest User")
                    self.pod_name = get_pod_info_in_cenm("cephfs-quotas-controller", self.cenm_namespace)
                    while self.keep_running():
                        self.sleep_until_day()
                        self.perform_fs_quotas_operations()
            else:
                raise EnvironError("{0} profile will run on cenm deployments only.".format(self.NAME))
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_fs_quotas_operations(self):
        """
        This function used to perform fs quotas operations.
        get_list_of_scripting_service_ips,
        Log in to scripting server and create cephtest user home directory,
        update ceph quotas config,
        check cephtest user quotas attributes,
        get ceph quotas config,
        create 3 dummy files for ceph user in scripting pod's

        :raises EnvironError: General scripting pods ip's are not found.
       """
        try:
            self.scripting_service_ip_list = get_list_of_scripting_service_ips()
            log.logger.debug("scripting services ip list: {0}".format(self.scripting_service_ip_list))
            if not self.scripting_service_ip_list:
                raise EnvironError("The general scripting pods ip's are not found in this deployment.")
            self.teardown_list.append(picklable_boundmethod(self.delete_ceph_user_home_dir))
            self.teardown_list.append(picklable_boundmethod(self.disable_ceph_quota_for_user))

            end_time = self.get_end_time()
            num_of_iterations = int((end_time - datetime.now()).total_seconds() / 600)
            log.logger.debug("num_of_iterations: {0}".format(num_of_iterations))

            for iteration in range(1, num_of_iterations + 1):
                log.logger.debug("# Iteration: {0}".format(iteration))
                log.logger.debug("Previously general scripting service ip: '{0}', port: {1} used to create the {2} "
                                 "user home directory.".format(self.scripting_service_ip_list[0],
                                                               self.last_used_scripting_service_port, self.USER_NAME))
                if self.last_used_scripting_service_port:
                    log.logger.debug("Deleting files in {0}: {1} general scripting "
                                     "service".format(self.scripting_service_ip_list[0],
                                                      self.last_used_scripting_service_port))
                    self.disable_ceph_quota_for_user()
                    self.delete_ceph_user_home_dir()

                self.currently_used_scripting_service_port = (self.SCRIPTING_SERVICE_PODS_PORTS[
                    self.scripting_service_ports_index])
                self.last_used_scripting_service_port = self.currently_used_scripting_service_port
                # update scripting service index to pick the another (random) scripting_service_ip port
                self.scripting_service_ports_index = ((self.scripting_service_ports_index + 1) %
                                                      len(self.SCRIPTING_SERVICE_PODS_PORTS))

                self.login_to_scripting_server_and_create_home_dir()
                payload = {"file": "quotaEnabled=true\nsizeGenericQuota=0\n{0}={1}\n".format(self.USER_NAME,
                                                                                             self.CEPH_QUOTA_LIMIT)}
                self.update_ceph_quotas_config(payload)
                self.check_ceph_quotas_attributes()
                self.get_ceph_quotas_config()
                self.create_dummy_files_for_ceph_user(3)
                self.log_results_of_current_iteration()
                if num_of_iterations - iteration != 0:
                    log.logger.debug("Sleeping for 600 seconds before run the "
                                     "next iteration: {0}.".format(iteration + 1))
                    time.sleep(600)
        except Exception as e:
            self.add_error_as_exception(e)

    def login_to_scripting_server_and_create_home_dir(self):
        """
        Log into scripting server with ceph user and create home directory with this user.

        :raises EnvironError: Unable to log in to scripting server with ceph user.
        """
        verify_and_remove_ssh_keys("{0}:{1}".format(self.scripting_service_ip_list[0],
                                                    self.currently_used_scripting_service_port))

        log.logger.debug("Currently {0} general scripting service ip, port: {1} used to create the {2} home "
                         "directory.".format(self.scripting_service_ip_list[0],
                                             self.currently_used_scripting_service_port, self.USER_NAME))
        child = pexpect.spawn('ssh -o StrictHostKeyChecking=no {0}@{1} '
                              '-p {2}'.format(self.USER_NAME, self.scripting_service_ip_list[0],
                                              self.currently_used_scripting_service_port), timeout=30)
        password_format = "[pP]assword:"
        auth_prompt = "Are you sure you want to continue connecting (yes/no)?"

        result = child.expect([auth_prompt, password_format, pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            log.logger.debug("Confirming connection: yes")
            child.sendline("yes")
            result = child.expect([auth_prompt, password_format, "{0}@".format(self.USER_NAME), pexpect.EOF,
                                   pexpect.TIMEOUT])
        if result == 1:
            log.logger.debug("Issuing password")
            child.sendline(self.user.password)
            result = child.expect([auth_prompt, password_format, "{0}".format(self.USER_NAME), pexpect.EOF,
                                   pexpect.TIMEOUT])
        if result == 2 and "Creating directory" in str(child.before):
            log.logger.debug("Successfully {0} user logged into scripting pod: {1}:{2} and created user "
                             "home directory".format(self.USER_NAME, self.scripting_service_ip_list[0],
                                                     self.currently_used_scripting_service_port))
        else:
            raise EnvironError("Problem encountered {0} user logged into scripting "
                               "pod: {1}:{2} due to {3}".format(self.USER_NAME,
                                                                self.scripting_service_ip_list[0],
                                                                self.currently_used_scripting_service_port,
                                                                child.before))

    def update_ceph_quotas_config(self, payload, action="config"):
        """
        Configure and remove the ceph quotas for ceph user.
        :return: json response of Configure and remove the ceph quotas.
        :param: payload: payload for to configure or remove the ceph quotas for ceph user.
        :type: payload: dict
        :param: action: default action is config. remove. action parameter used to update the log statements clearly.
        :type: action: str

        :rtype: dict
        :raises EnmApplicationError: Failed to configure the ceph quotas for ceph user.
        """
        log.logger.debug("Attempting to {0} the ceph quotas for {1} user ".format(action, self.user.username))
        log.logger.debug("Ceph quotas {0} payload: {1}".format(action, payload))
        response = self.user.post(WRITE_QUOTA_CONFIG_URL, files=payload,
                                  headers={"X-Tor-UserID": self.user.username})
        response.raise_for_status()
        json_response = response.text
        log.logger.debug("Response of ceph quotas {0}: {1}".format(
            "configuration" if action == "config" else action, json_response))
        if response.status_code != 200:
            raise EnmApplicationError("Failed to {0} the ceph quotas due to {1}".format(action, json_response))
        log.logger.debug(
            "Successfully {0}d ceph quotas  for {1} user : {2}".format(
                "configure" if action == "config" else action, self.user.username, json_response))
        log.logger.debug("Sleeping for 10 seconds to apply the ceph quota {0}d attributes".format(
            "configure" if action == "config" else action))
        time.sleep(10)
        self.check_profile_memory_usage()

        return json_response

    def get_ceph_quotas_config(self):
        """
        Get ceph quotas configuration for ceph user.
        :return: json response of ceph quotas configuration.
        :rtype: dict
        :raises EnmApplicationError: Failed to get the ceph quotas configuration for ceph user.
        """
        log.logger.debug("Attempting to get the ceph quotas configuration for {0} user ".format(self.user.username))
        response = self.user.get(READ_QUOTA_CONFIG_URL, headers={"X-Tor-UserID": self.user.username})
        response.raise_for_status()
        json_response = response.text
        log.logger.debug("Response of ceph quotas configuration: {0}".format(json_response))
        if response.status_code != 200:
            raise EnmApplicationError("Failed to get the ceph quotas configuration due to {0}".format(json_response))
        log.logger.debug(
            "Successfully Fetched configured ceph quotas configuration for {0} user : {1}".format(
                self.user.username, json_response))
        self.check_profile_memory_usage()

        return json_response

    def check_ceph_quotas_attributes(self):
        """
        Check if ceph quotas attributes are configured or not in cephfs-quotas-controller service pod.
        """
        log.logger.debug("Attempting to get the ceph quotas configured attributes for "
                         "{0} user".format(self.user.username))
        cmd = "getfattr -n ceph.quota.max_bytes /home/shared/{0}".format(self.USER_NAME)
        command_response = shell.run_cmd_on_cloud_native_pod("cephfs-quotas-controller", self.pod_name, cmd)
        log.logger.debug("Response of ceph quotas attributes: {0}, rc: {1}".format(command_response.stdout,
                                                                                   command_response.rc))
        if "No such attribute" in command_response.stdout:
            log.logger.debug("Attributes are not set. Again configure ceph quota limit for "
                             "{0} user".format(self.USER_NAME))

    def create_dummy_files_for_ceph_user(self, files_count):
        """
        Create dummy files based on files count in ceph user home directory in general scripting pod.
        :param: files_count: number of dummy files to create in scripting pod for this user.
        :type: files_count: int
        """
        child = pexpect.spawn('ssh -o StrictHostKeyChecking=no {0}@{1} -p {2}'.format(
            self.USER_NAME, self.scripting_service_ip_list[0],
            self.currently_used_scripting_service_port), timeout=120)
        password_format = "[pP]assword:"
        auth_prompt = "Are you sure you want to continue connecting (yes/no)?"

        result = child.expect([auth_prompt, password_format, pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            log.logger.debug("Confirming connection: yes")
            child.sendline("yes")
            result = child.expect([auth_prompt, password_format, "{0}@".format(self.USER_NAME), pexpect.EOF,
                                   pexpect.TIMEOUT])
        if result == 1:
            log.logger.debug("Issuing password")
            child.sendline(self.user.password)
            result = child.expect([auth_prompt, password_format, "{0}@".format(self.USER_NAME), pexpect.EOF,
                                   pexpect.TIMEOUT])
        if result == 2:
            log.logger.debug("Successfully {0} user logged into {1}:{2} and created user "
                             "home directory".format(self.USER_NAME, self.scripting_service_ip_list[0],
                                                     self.currently_used_scripting_service_port))
            log.logger.debug("Res: {0}".format(child.before))
            for file_index in range(files_count):
                if file_index == 2:  # Need to sleep 30 seconds before create the 3rd dummy file.
                    log.logger.debug(
                        "Sleeping for 30 seconds, before create dummy {0} file in {1} user home directory in "
                        "{2}:{3} scripting server.".format(file_index, self.USER_NAME,
                                                           self.scripting_service_ip_list[0],
                                                           self.currently_used_scripting_service_port))
                    time.sleep(30)
                child.sendline("truncate -s {0} /home/shared/cephtest_1/test_file_{1}".format(self.FILE_SIZE,
                                                                                              file_index))
                result = child.expect(["{0}@general".format(self.USER_NAME), "failed to truncate",
                                       pexpect.EOF, pexpect.TIMEOUT])
                log.logger.debug("Response: {0}, {1}".format(child.before, child.after))
                if result == 0:
                    log.logger.debug("Successfully created {0} dummy file.".format(file_index))
                if result == 1:
                    log.logger.debug("Unable to create {0} dummy file due to "
                                     "Disk quota exceeded.".format(file_index))
                    self.iteration_success = True
        self.check_profile_memory_usage()

    def create_cephtest_user_in_enm(self):
        """ Deprecated 23.16 Delete 24.11 JIRA:ENMRTD-23821 """

    def delete_ceph_user_home_dir(self):
        """
        Deletes the ceph user home directory in scripting pod.
        """
        verify_and_remove_ssh_keys("{0}:{1}".format(self.scripting_service_ip_list[0],
                                                    self.last_used_scripting_service_port))
        scripting_pod_name = ("general-scripting-0" if self.last_used_scripting_service_port == 5020 else
                              "general-scripting-1")
        log.logger.debug("Attempting to delete the ceph user: {0} home directory in {1} "
                         "scripting service pod".format(self.USER_NAME, scripting_pod_name))
        cmd = "rm -rf /home/shared/{0}".format(self.USER_NAME)
        response = shell.run_cmd_on_cloud_native_pod("general-scripting", scripting_pod_name, cmd)
        if response.rc != 0:
            log.logger.debug("Failed to delete the the ceph user: {0} home directory "
                             "in {1} scripting service pod due to {2}".format(self.USER_NAME, scripting_pod_name,
                                                                              response.stdout))
        log.logger.debug("Successfully deleted ceph user: {0} home directory in {1} "
                         "scripting service pod: {2}".format(self.USER_NAME, scripting_pod_name, response.stdout))
        self.check_profile_memory_usage()

    def disable_ceph_quota_for_user(self):
        """
        Disable the ceph quotas for ceph user
        """
        payload = {"file": "quotaEnabled=false\nsizeGenericQuota=0\n"}
        self.update_ceph_quotas_config(payload, "remove")
        self.check_profile_memory_usage()

    def log_results_of_current_iteration(self):
        """
        Log the results of the log stream received into sys log receiver.
        Logging is happening to daemon logs, via separate lines per instrumentation value
        """
        if self.iteration_success:
            log.logger.debug("{0} user result for ceph quota limit is working fine as per configuration, "
                             "scripting service ip: {1}: port: {2}, "
                             "RESULT: PASS".format(self.USER_NAME, self.scripting_service_ip_list[0],
                                                   self.currently_used_scripting_service_port))
        else:
            log.logger.debug("{0} user result for ceph quota limit is not working fine as per configuration, "
                             "scripting service ip: {1}: port: {2}, "
                             "RESULT: FAIL".format(self.USER_NAME, self.scripting_service_ip_list[0],
                                                   self.currently_used_scripting_service_port))

    def verify_whether_deployment_type_is_cnis(self):
        """
        Verify whether deployment type is CNIS or not.

        :returns: true, if deployment type is CNIS
        :rtype: bool

        :raises EnvironError: It will raise the EnvironError, When cenm deployment type is not a CNIS.
        """
        _, deployment_hostname = get_hostname_in_cloud_native()
        deployment_name = deployment_hostname.split('_')[0]
        cenm_deployment_values_doc_id = fetch_cenm_deployment_values_id(deployment_name)
        cenm_deployment_type = fetch_cenm_deployment_type(cenm_deployment_values_doc_id)
        if cenm_deployment_type != "CNIS":
            raise EnvironError("This cenm deployment is not a CNIS deployment. "
                               "Profile is supported to run on CNIS cenm deployments.")
        else:
            log.logger.debug("{0} is a CNIS cenm deployment".format(deployment_name))
            return True


def fetch_cenm_deployment_values_id(deployment_name):
    """
    Fetches the cenm_deployment_values id from DIT

    :param deployment_name: String containing name of deployment passed to script
    :type deployment_name: str
    :return: String containing the cenm_deployment_values document id.
    :rtype: str
    """
    log.logger.info("Querying DIT API to fetch cenm deployment values id ...\n")
    url_to_get_cenm_deployment_values_id = r"{dit_url}/api/deployments/?q=name={deployment_name}\&fields=documents" \
        .format(dit_url=DIT_URL, deployment_name=deployment_name)
    log.logger.debug("Get cenm deployment values id dit rest api: {0}".format(url_to_get_cenm_deployment_values_id))
    curl_command_to_get_cenm_deployment_values_id = "curl -s {0}".format(url_to_get_cenm_deployment_values_id)
    try:
        response = subprocess.check_output(curl_command_to_get_cenm_deployment_values_id,
                                           stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        log.logger.debug("Problem encountered during command execution: {0}\n - {1}".format(e, e.output))
        return ""

    if response.rstrip():
        return parse_cenm_deployment_values_id_data(response, curl_command_to_get_cenm_deployment_values_id)
    return ""


def parse_cenm_deployment_values_id_data(response, curl_command_to_get_cenm_deployment_values_id):
    """
    Parses curl response to extract cenm deployment values document id

    :param response: Curl response
    :type response: str
    :param curl_command_to_get_cenm_deployment_values_id: Curl command used
    :type curl_command_to_get_cenm_deployment_values_id: str
    :return: String containing cenm deployment values id
    :rtype: str
    """
    cenm_deployment_values_id = ""
    try:
        json_data = json.loads(response)
    except ValueError:
        return ""

    if json_data and isinstance(json_data, list) and "documents" in json_data[0].keys():
        for item in json_data[0]["documents"]:
            if "schema_name" in item.keys() and item["schema_name"] == "cenm_deployment_values":
                cenm_deployment_values_id = item["document_id"]

    if not cenm_deployment_values_id:
        log.logger.debug("Could not get cenm_deployment_values_id from DIT using command: {0}\n".format(
            curl_command_to_get_cenm_deployment_values_id))
        return ""

    return cenm_deployment_values_id


def fetch_cenm_deployment_type(cenm_deployment_values_id):
    """
    Fetches the cenm deployment type from DIT

    :param cenm_deployment_values_id: String containing the cenm_deployment_values id
    :type cenm_deployment_values_id: str
    :return: String containing the cenm_deployment_type. EX: CNIS
    :rtype: str
    """
    cenm_deployment_type = ""

    log.logger.info("Querying DIT API to fetch cenm deployment type ...\n")
    url_to_get_cenm_deployment_type = (r"{dit_url}/api/documents/{cenm_deployment_values_id}?"
                                       r"fields=content/parameters/cenm_deployment_type".format(dit_url=DIT_URL,
                                                                                                cenm_deployment_values_id=cenm_deployment_values_id))
    log.logger.debug("Get cenm deployment type dit rest api: {0}".format(url_to_get_cenm_deployment_type))
    curl_command_to_get_cenm_deployment_type = "curl -s {0}".format(url_to_get_cenm_deployment_type)

    try:
        response = subprocess.check_output(curl_command_to_get_cenm_deployment_type, stderr=subprocess.STDOUT,
                                           shell=True)
    except subprocess.CalledProcessError as e:
        log.logger.debug("Problem encountered during command execution: {0}\n - {1}".format(e, e.output))
        return ""

    if response.rstrip():
        try:
            json_data = json.loads(response)
        except ValueError:
            return ""

        if (json_data and "content" in json_data.keys() and "parameters" in json_data["content"] and
                json_data["content"]["parameters"] and "cenm_deployment_type" in json_data["content"]["parameters"]):
            cenm_deployment_type = json_data["content"]["parameters"]["cenm_deployment_type"]

    if not cenm_deployment_type:
        log.logger.debug("Unable to get Workload VM hostname for deployment from DIT using command: {0}\n".format(
            curl_command_to_get_cenm_deployment_type))
        return ""

    return cenm_deployment_type


def verify_and_remove_ssh_keys(ip_with_port):
    """
    verify and remove ssh keys in known_hosts file on workload VM.
    :param ip_with_port: scripting pod ip with port
    :type ip_with_port: str
    """
    log.logger.debug("Removing scripting VIP from known_hosts file on workload VM as "
                     "'Host key verification' failures can sometimes occur while using ssh-copy-id towards VIP, "
                     "due to host changes on the cluster")
    shell.run_local_cmd(shell.Command("ssh-keygen -R {0}".format(ip_with_port)))
