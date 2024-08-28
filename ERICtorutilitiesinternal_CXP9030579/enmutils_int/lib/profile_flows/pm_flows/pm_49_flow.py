import json
import time
import datetime
from functools import partial
import pexpect
from enmutils.lib import log, shell, cache
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.enm_deployment import get_values_from_global_properties
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow import get_pod_info_in_cenm
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm, update_pib_parameter_on_enm


CONFIGURE_USER = "useradd -m {user_name};echo \"{password}\" | passwd --stdin {user_name};echo \"{user_name}\" | tee -a /etc/vsftpd/user_list"

PUSH_FILE_TRANSFER_CMD = "pushfiletransfer {action}"
PUSH_FILE_TRANSFER_ENABLE_CMD = ("{0} --ipaddress {server_ip} --username {username} --password {password} --cmbulkgenstarttime "
                                 "{timestamp_in_hh_mm_ss}{1}")

PUSH_FILE_TRANSFER_ENABLE_VERIFICATION = "PushService is Enabled."
PUSH_FILE_TRANSFER_DISABLE_VERIFICATION = "PushService is Disabled."

DISABLE_PUSHSERVICE_RANDOMTIME_NOT_FOUND_VERIFICATION = '''Management resource '[(\"system-property\" => \"DISABLE_PUSHSERVICE_RANDOMTIME\")]' not found'''
ENABLE_END_POINT_CHECKING_NOT_FOUND_VERIFICATION = '''Management resource '[(\"system-property\" => \"ENABLE_END_POINT_CHECKING\")]' not found'''
TRANSFER_ONLY_NOT_STORE_FILES_NOT_FOUND_VERIFICATION = '''Management resource '[(\"system-property\" => \"TRANSFER_ONLY_NOT_STORE_FILES\")]' not found'''
USE_DUMMY_CCPDSERVICE_MO_NOT_FOUND_VERIFICATION = '''Management resource '[(\"system-property\" => \"USE_DUMMY_CCPDSERVICE_MO\")]' not found'''

GET_VAULT_TOKEN_CMD = 'curl -s -k -X GET -H "Content-Type:application/json" https://vault-service:8107/vault-service/1.0/token'
POST_GENERATAED_KEY_USING_VAULT_TOKEN = '''curl -s -k -H "Content-Type: application/json" -H "Vault-Token:{token}" -X POST https://vault-service:8107/vault-service/1.0/secret/pushservice/generatedKey/ -d @/tmp/PushService_PrivateKey.json'''

GET_DISABLE_PUSHSERVICE_RANDOMTIME_VALUE_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=DISABLE_PUSHSERVICE_RANDOMTIME:read-resource' --output-json")
GET_ENABLE_END_POINT_CHECKING_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=ENABLE_END_POINT_CHECKING:read-resource' --output-json")
GET_TRANSFER_ONLY_NOT_STORE_FILES_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=TRANSFER_ONLY_NOT_STORE_FILES:read-resource' --output-json")
GET_USE_DUMMY_CCPDSERVICE_MO_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=USE_DUMMY_CCPDSERVICE_MO :read-resource' --output-json")

ADD_DISABLE_PUSHSERVICE_RANDOMTIME_VALUE_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=DISABLE_PUSHSERVICE_RANDOMTIME:add(value={action})' --output-json")
ADD_ENABLE_END_POINT_CHECKING_VALUE_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=ENABLE_END_POINT_CHECKING:add(value={action})' --output-json")
ADD_TRANSFER_ONLY_NOT_STORE_FILES_VALUE_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=TRANSFER_ONLY_NOT_STORE_FILES:add(value={action})' --output-json")
ADD_USE_DUMMY_CCPDSERVICE_MO_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=USE_DUMMY_CCPDSERVICE_MO:add(value={action})' --output-json")

REMOVE_DISABLE_PUSHSERVICE_RANDOMTIME_PROPERTY_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=DISABLE_PUSHSERVICE_RANDOMTIME:remove' --output-json")
REMOVE_ENABLE_END_POINT_CHECKING_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=ENABLE_END_POINT_CHECKING:remove' --output-json")
REMOVE_TRANSFER_ONLY_NOT_STORE_FILES_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=TRANSFER_ONLY_NOT_STORE_FILES:remove' --output-json")
REMOVE_USE_DUMMY_CCPDSERVICE_MO_CMD = ("{0}/ericsson/3pp/jboss/bin/jboss-cli.sh -c './system-property=USE_DUMMY_CCPDSERVICE_MO:remove' --output-json")
KUBECTL_CMD = '/usr/local/bin/kubectl --kubeconfig /root/.kube/config exec -n {0} {1} -c pushservice -- bash -c "{2}" 2>/dev/null'
SUDO = "sudo "

EXPIRY_TIME_TO_VERIFY_THE_PRODUCT_DATA_ENABLE_STATUS = 100 * 60  # 100 minutes (1hrs 40 minutes)
EXPIRY_TIME_TO_VERIFY_THE_PRODUCT_DATA_DISABLE_STATUS = 5.5 * 60 * 60  # 5.5 hours (330 minutes)
SLEEP_TIME_TO_VERIFY_THE_PRODUCT_DATA_ENABLED_STATUS = 15 * 60  # 15 minutes (900 seconds)
SLEEP_TIME_TO_VERIFY_THE_PRODUCT_DATA_DISABLED_STATUS = 30 * 60  # 30 minutes (1800 seconds)


class Pm49Flow(GenericFlow):

    def __init__(self):
        """
        Init Method
        """
        super(Pm49Flow, self).__init__()
        self.user = []
        self.push_service_ip = ""
        self.is_cloud_native = None
        self.cenm_namespace = None

    def execute_flow(self):
        """
        Main flow for PM PM_49
        """
        try:
            self.cenm_namespace = cache.get_enm_cloud_native_namespace()
            self.is_cloud_native = cache.is_enm_on_cloud_native()
            self.user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
            self.state = 'RUNNING'
            if cache.check_if_on_workload_vm():
                self.push_service_ip = self.get_push_service_ip()
                self.ftpes_setup_on_vm(self.user, self.push_service_ip, self.PUSH_SERVICE_TERMINATE_VM_IP)
                disable_random_time_on_push_service_status = self.disable_random_time_on_push_service()
                disable_end_point_checking_on_push_service_status = self.disable_end_point_checking_on_push_service()
                enable_transfer_only_not_store_files_on_push_service_status = \
                    self.enable_transfer_only_not_store_files_on_push_service()
                enable_use_dummy_ccpdservice_mo_on_push_service_status = self.enable_use_dummy_ccpdservice_mo_on_push_service()
                self.set_fntpushebsfiles_pib_active()
                push_service_statuses = all([disable_random_time_on_push_service_status,
                                             disable_end_point_checking_on_push_service_status,
                                             enable_transfer_only_not_store_files_on_push_service_status,
                                             enable_use_dummy_ccpdservice_mo_on_push_service_status])
                if push_service_statuses:
                    self.execute_tasks()
            else:
                raise EnvironError("Profile is not running on workload vm")
        except Exception as e:
            self.add_error_as_exception(e)

    def ftpes_setup_on_vm(self, user, push_service_ip, push_service_terminate_vm_ip):
        """
        This method will do following operations,
        Calls initial setup method,
        Calls post private key method,
        Import SubCA, EE certificates for ftpes client
        :param user: Profile User
        :type user: Any
        :param push_service_ip: Pushservice IP/pod name
        :type push_service_ip: str
        :param push_service_terminate_vm_ip: Pushservice Terminate VM IP (Default: 10.232.47.72)
        :type push_service_terminate_vm_ip: str
        :raises EnvironError: if CA and EE certificate is failed
        """
        self.intial_setup_of_ftpes_on_pushservice_terminate_vm(user, push_service_terminate_vm_ip)
        self.post_private_key_to_vault_on_pushservice_sg(push_service_ip)
        import_ca_file = user.enm_execute('pushfiletransfer crtimport --ca file:"TESTTLSSubCA.pem"',
                                          file_in=get_internal_file_path_for_import("etc", "pm_49_ftpes_setup_files",
                                                                                    "TESTTLSSubCA.pem"))
        log.logger.debug("Output response for CA certificate:{0}".format(import_ca_file.get_output()))
        ca_file_import_status = "SUCCESS" if "Imported" in import_ca_file.get_output()[1] else "FAILED"
        log.logger.debug("CA certificate is Imported: {0}".format(ca_file_import_status))
        import_ee_file = user.enm_execute('pushfiletransfer crtimport --ee file:"TESTTLSPushService.pem"',
                                          file_in=get_internal_file_path_for_import("etc", "pm_49_ftpes_setup_files",
                                                                                    "TESTTLSPushService.pem"))
        log.logger.debug("Output response for EE certificate:{0}".format(import_ee_file.get_output()))
        ee_file_import_status = "SUCCESS" if "Imported" in import_ee_file.get_output()[1] else "FAILED"
        log.logger.debug("EE certificate is Imported: {0}".format(ee_file_import_status))
        if ee_file_import_status != "SUCCESS" and ca_file_import_status != "SUCCESS":
            raise EnvironError("Importing CA and EE certificates failed!!")
        else:
            log.logger.debug("Successfully imported CA and EE certificates !!!")

    def intial_setup_of_ftpes_on_pushservice_terminate_vm(self, user, push_service_terminate_vm_ip):
        """
        Verify vsftpd is installed or not, if not it will install it.
        Creates user, sets password for user, check user in user_list
        Start and enable vsftpd on wlvm
        Create private_key_json file on pushservice to use in post curl command
        Post Private Key to Vault using curl commands
        :param user: Profile User
        :type user: Any
        :param push_service_terminate_vm_ip: Pushservice Terminate VM IP
        :type push_service_terminate_vm_ip: str
        :raises EnvironError: if we get any one response code as 1
        """
        log.logger.debug('Initial setup of FTPES on pushservice terminate VM has started..')
        check_vsftpd_installed = shell.run_cmd_on_vm(shell.Command("yum list installed| grep vsftpd"), user='root',
                                                     password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                                     vm_host=push_service_terminate_vm_ip)
        if not check_vsftpd_installed.stdout and check_vsftpd_installed.rc:
            vsftpd_installation = shell.run_cmd_on_vm(shell.Command("yum -y install vsftpd"), user='root',
                                                      password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                                      vm_host=push_service_terminate_vm_ip)
            log.logger.debug("Return code for vsftpd installation:{0}\nInstalled vsftpd successfully !!"
                             "".format(vsftpd_installation.rc))
        else:
            log.logger.debug("vsftpd is already installed !!")
        add_user = shell.run_cmd_on_vm(shell.Command("useradd -m {0}".format(user.username)), user='root',
                                       password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                       vm_host=push_service_terminate_vm_ip)
        set_password = shell.run_cmd_on_vm(shell.Command("echo \"{0}\" | passwd --stdin {1}".format(
            user.password, user.username)), user='root', password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD, vm_host=push_service_terminate_vm_ip)
        user_check_exists = shell.run_cmd_on_vm(shell.Command("echo \"{0}\" | tee -a /etc/vsftpd/user_list".format(
            user.username)), user='root', password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD, vm_host=push_service_terminate_vm_ip)

        # Copy Certificates to Pushservice Terminate VM and update vsftpd.conf file
        self.copy_certificates_to_pushservice_terminate_vm(push_service_terminate_vm_ip)
        systemctl_start = shell.run_cmd_on_vm(shell.Command("systemctl start vsftpd.service"), user='root',
                                              password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                              vm_host=push_service_terminate_vm_ip)
        systemctl_enable = shell.run_cmd_on_vm(shell.Command("systemctl enable vsftpd.service"), user='root',
                                               password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                               vm_host=push_service_terminate_vm_ip)
        if any([add_user.rc, set_password.rc, user_check_exists.rc, systemctl_start.rc, systemctl_enable.rc]):
            raise EnvironError("Error occurred during FTPES setup on pushservice terminate VM")
        else:
            log.logger.debug("Intial setup of FTPES on pushservice terminate VM has done successfully")

    def post_private_key_to_vault_on_pushservice_sg(self, push_service_ip):
        """
        Post private key to Vault on Pushservice
        :param push_service_ip: Pushservice Terminate VM IP (Default: 10.232.47.72)
        :type push_service_ip: str
        :raises EnvironError: if Post private key to Vault on Pushservice is failed.
        """
        vault_token = self.get_vault_token_from_push_service()
        create_private_key_json_file_on_pushservice_vm = self.create_pushservice_privateKey_file_on_push_service()
        post_private_key_to_vault = self.post_private_key_to_vault_on_pushservice(vault_token)
        if any([vault_token.rc, create_private_key_json_file_on_pushservice_vm.rc, post_private_key_to_vault.rc]):
            raise EnvironError("Error occurred during Post private key to vault on Pushservice.")
        else:
            log.logger.debug("Post private key to vault on Pushservice was successfully.")

    def copy_certificates_to_pushservice_terminate_vm(self, push_service_terminate_vm_ip):
        """
        Copies Private Key, Certificate, CA Certificate, vsftpd.conf to /etc/vsftpd/
        folder on Pushservice Terminate VM
        :param push_service_terminate_vm_ip: Pushservice Terminate VM IP
        :type push_service_terminate_vm_ip: str
        :raises EnvironError: if file copying is failed.
        """
        list_of_files = ["vsftpd.pem", "vsftpd.key", "vsftpd_ca_bundle.pem", "vsftpd.conf"]
        file_copy_status = []
        log.logger.debug('Copying Certificates to pushservice terminate vm..')
        for file_name in list_of_files:
            log.logger.debug("Copying {0} to /etc/vsftpd on pushservice terminate vm {1}".format(
                file_name, push_service_terminate_vm_ip))
            copy_certificates = pexpect.spawn("scp -r {0} root@{1}:/etc/vsftpd/".format(
                get_internal_file_path_for_import("etc", "pm_49_ftpes_setup_files", "{}".format(file_name)),
                push_service_terminate_vm_ip))
            rc_adding_key_fingerprint = copy_certificates.expect(['Are you sure you want to continue connecting',
                                                                  pexpect.EOF, pexpect.TIMEOUT])
            if rc_adding_key_fingerprint == 0:
                log.logger.debug("Allowing to add key fingerprint")
                copy_certificates.sendline("yes")
            else:
                log.logger.debug("Already keys are added !!")
            rc_password = copy_certificates.expect(['password', pexpect.EOF, pexpect.TIMEOUT])
            log.logger.debug("Return code for password:{0}".format(rc_password))
            if rc_password == 0:
                log.logger.debug("Enter password for root@{0}".format(push_service_terminate_vm_ip))
                copy_certificates.sendline(self.PUSH_SERVICE_TERMINATE_VM_PASSWORD)
            else:
                log.logger.debug("Password not required")
            rc_copy_status = copy_certificates.expect(['{0}'.format(file_name), pexpect.EOF, pexpect.TIMEOUT])
            log.logger.debug("Return code for copy status:{0}".format(rc_copy_status))
            if rc_copy_status == 0:
                log.logger.debug("Successfully copied {0}".format(file_name))
            else:
                log.logger.debug("Failed to copy {0}".format(file_name))
            file_copy_status.append(rc_copy_status)
        if any(file_copy_status):
            raise EnvironError("Error occurred during copying certificates to pushservice terminate VM")
        else:
            log.logger.debug("Successfully copied files {0}".format(list_of_files))

    def enable_and_disable_push_file_transfer_service(self, action, is_product_data_required=True):
        """
        Enable or disable push file transfer service

        :param action: enable, disable
        :type action: str
        :param is_product_data_required: --productdata flag need to add enable pushfiletransfer command,
                                         when is_product_data_required is True
        :type is_product_data_required: bool
        :raises EnmApplicationError: if pushfiletransfer enable/disable operation is failed.
        """
        log.logger.debug("Attempting to {0} the push file transfer on {1}".format(action,
                                                                                  self.PUSH_SERVICE_TERMINATE_VM_IP))
        self.get_status_of_push_file_transfer_service(action)
        cmd_verification = (PUSH_FILE_TRANSFER_ENABLE_VERIFICATION if action == "enable" else
                            PUSH_FILE_TRANSFER_DISABLE_VERIFICATION)
        if action == "enable":
            cmd = PUSH_FILE_TRANSFER_ENABLE_CMD.format(PUSH_FILE_TRANSFER_CMD.format(action=action),
                                                       " --productdata" if is_product_data_required else "",
                                                       server_ip=self.PUSH_SERVICE_TERMINATE_VM_IP,
                                                       username=self.user.username, password=self.user.password,
                                                       timestamp_in_hh_mm_ss=self.CM_BULK_GEN_START_TIME)
            message = ("Successfully Enabled Push File Transfer Service on {0} with {1}".format(
                self.PUSH_SERVICE_TERMINATE_VM_IP, self.user.username))
        else:
            self.enable_use_dummy_ccpdservice_mo_on_push_service()
            cmd = PUSH_FILE_TRANSFER_CMD.format(action=action)
            message = "Successfully Disabled Push File Transfer Service on {0} with {1}".format(
                self.PUSH_SERVICE_TERMINATE_VM_IP, self.user.username)

        response = self.user.enm_execute(cmd)
        if response and cmd_verification not in " ".join(response.get_output()):
            raise EnmApplicationError("Unable to {0} pushfiletransfer on {1} with {2} "
                                      ": {3}".format(action, self.PUSH_SERVICE_TERMINATE_VM_IP, self.user.username,
                                                     " ".join(response.get_output())))
        log.logger.debug(message)
        self.get_status_of_push_file_transfer_service(action)
        if action != "disable":
            self.wait_product_data_to_enable_disable_state(("Enabled" if action == "enable" else "Disabled"))

    def get_status_of_push_file_transfer_service(self, action):
        """
        Get status of push file transfer service

        :param action: enable, disable
        :type action: str
        :raises EnmApplicationError: if Error occurred while getting the push file transfer service status.
        """
        log.logger.debug("Attempting to get the push file transfer service status")
        cmd = PUSH_FILE_TRANSFER_CMD.format(action="status")
        log.logger.debug("Execute {0} command to get the push file transfer service status".format(cmd))
        response = self.user.enm_execute(cmd)
        action_status = "Active" if action == "enable" else "Inactive"
        if response and "Error" in "\n".join(response.get_output()):
            raise EnmApplicationError("Error occurred while getting the push file transfer service status "
                                      "due to {0}".format(response.get_output()))
        log.logger.debug("Successfully fetched push file transfer service "
                         "status: {0}".format(" ".join(response.get_output())))
        if action_status in " ".join(response.get_output()):
            log.logger.debug("Successfully {0}d push file transfer service on {1}".format(
                action, self.PUSH_SERVICE_TERMINATE_VM_IP))

    def get_status_of_push_file_transfer(self):
        """
        Get status of push file transfer service
        :return: push file transfer service status
        :rtype: str

        :raises EnmApplicationError: if Error occurred while getting the push file transfer service status.
        """
        log.logger.debug("Attempting to get the push file transfer service status")
        cmd = PUSH_FILE_TRANSFER_CMD.format(action="status")
        log.logger.debug("Execute {0} command to get the push file transfer service status".format(cmd))
        response = self.user.enm_execute(cmd)
        if response and "Error" in "\n".join(response.get_output()):
            raise EnmApplicationError("Error occurred while getting the push file transfer service status "
                                      "due to {0}".format(response.get_output()))
        log.logger.debug("Successfully fetched push file transfer service "
                         "status: {0}".format(" ".join(response.get_output())))
        return response.get_output()

    def ftpes_setup_on_vm_teardown(self):
        """
        Removes SubCA and EE certicate from push service VM.
        """
        user_deleted_flag, retry_count, delete_user = True, 3, None
        while user_deleted_flag:
            delete_user = shell.run_cmd_on_vm(shell.Command("userdel -r {0}".format(self.user.username)),
                                              user='root', password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                              vm_host=self.PUSH_SERVICE_TERMINATE_VM_IP)
            log.logger.debug("Output for userdel: {0}".format(delete_user.stdout))
            if 'userdel:' in delete_user.stdout:
                log.logger.debug("User was not deleted because of error:{}".format(delete_user.stdout))
                retry_count -= 1
                log.logger.debug("Retrying to delete user again...\nRetries remaining: {0}\nWaiting for 2 minutes..."
                                 "".format(retry_count))
                time.sleep(120)
                if retry_count == 0:
                    user_deleted_flag = False
            else:
                user_deleted_flag = False
        delete_userlist = shell.run_cmd_on_vm(shell.Command("sed -i '/{0}/d' "
                                                            "/etc/vsftpd/user_list".format(self.user.username)),
                                              user='root', password=self.PUSH_SERVICE_TERMINATE_VM_PASSWORD,
                                              vm_host=self.PUSH_SERVICE_TERMINATE_VM_IP)
        log.logger.debug("Output for userlist del: {0}".format(delete_userlist.stdout))
        remove_certificates = self.user.enm_execute('pushfiletransfer crtdelete')
        log.logger.debug("Output for removing certificates:{}".format(remove_certificates.get_output()))
        remove_certificates_status = "SUCCESS" if "Deleted" in remove_certificates.get_output()[1] else "FAILED"
        log.logger.debug("CA and EE certificates has been Removed/Deleted: {}".format(remove_certificates_status))
        if delete_user.rc or delete_user.stdout:  # when rc is 0 and stdout has some message that means user not deleted
            raise EnvironError("Unable to delete {0} and remove {0} from user_list!!".format(self.user.username))
        else:  # when rc is 0 and no stdout returned that means user deleted successfully
            log.logger.debug("Successfully deleted {0} and removed {0} from user_list!!".format(self.user.username))

    def get_push_service_ip(self):
        """
        Get the push service ip/pod name from enm on physical/cenm.
        :return: push service ip
        :rtype: str
        :raises EnvironError: DB vms are not available in ENM
        """
        if self.is_cloud_native:
            push_service_ip = get_pod_info_in_cenm("pushservice", self.cenm_namespace)
        else:
            push_service_ips = get_values_from_global_properties("pushservice")
            if not push_service_ips:
                raise EnvironError("Push service is not available in ENM")
            push_service_ip = push_service_ips[0]
        return push_service_ip

    def get_disable_pushservice_randomtime_configured_value(self):
        """
        Get the DISABLE_PUSHSERVICE_RANDOMTIME configured value from push service.

        :return: DISABLE_PUSHSERVICE_RANDOMTIME value
        :rtype: str
        :raises EnvironError: Unable to get DISABLE_PUSHSERVICE_RANDOMTIME value from push service
        """
        log.logger.debug("Attempt to get the disable push service random time configured value")
        command = GET_DISABLE_PUSHSERVICE_RANDOMTIME_VALUE_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)
        if (response.rc == 0 and response.stdout and json.loads(response.stdout)["outcome"] == "success" and
                "result" in json.loads(response.stdout) and "value" in json.loads(response.stdout)["result"]):
            return json.loads(response.stdout)["result"]["value"]
        elif (response.rc == 1 and response.stdout and json.loads(response.stdout)["outcome"] == "failed" and
              DISABLE_PUSHSERVICE_RANDOMTIME_NOT_FOUND_VERIFICATION in
              json.loads(response.stdout)["failure-description"]):
            log.logger.debug("DISABLE_PUSHSERVICE_RANDOMTIME system property not found on "
                             "push service({0})".format(self.push_service_ip))
            return "FALSE"
        else:
            raise EnvironError("Unable to get DISABLE_PUSHSERVICE_RANDOMTIME value from "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def get_enable_end_point_checking_configured_value(self):
        """
        Get the ENABLE_END_POINT_CHECKING configured value from push service.

        :return: ENABLE_END_POINT_CHECKING value
        :rtype: str
        :raises EnvironError: Unable to get ENABLE_END_POINT_CHECKING value from push service
        """
        log.logger.debug("Attempt to get the enable_end_point_checking configured value")
        command = GET_ENABLE_END_POINT_CHECKING_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if (response.rc == 0 and response.stdout and json.loads(response.stdout)["outcome"] == "success" and
                "result" in json.loads(response.stdout) and "value" in json.loads(response.stdout)["result"]):
            return json.loads(response.stdout)["result"]["value"]
        elif (response.rc == 1 and response.stdout and json.loads(response.stdout)["outcome"] == "failed" and
              ENABLE_END_POINT_CHECKING_NOT_FOUND_VERIFICATION in
              json.loads(response.stdout)["failure-description"]):
            log.logger.debug("ENABLE_END_POINT_CHECKING system property not found on "
                             "push service({0})".format(self.push_service_ip))
            return "FALSE"
        else:
            raise EnvironError("Unable to get ENABLE_END_POINT_CHECKING value from "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def get_transfer_only_not_store_files_value(self):
        """
        Get the TRANSFER_ONLY_NOT_STORE_FILES configured value from push service.

        :return: TRANSFER_ONLY_NOT_STORE_FILES value
        :rtype: str
        :raises EnvironError: Unable to get TRANSFER_ONLY_NOT_STORE_FILES value from push service
        """
        log.logger.debug("Attempt to get the TRANSFER_ONLY_NOT_STORE_FILES configured value")
        command = GET_TRANSFER_ONLY_NOT_STORE_FILES_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if (response.rc == 0 and response.stdout and json.loads(response.stdout)["outcome"] == "success" and
                "result" in json.loads(response.stdout) and "value" in json.loads(response.stdout)["result"]):
            return json.loads(response.stdout)["result"]["value"]
        elif (response.rc == 1 and response.stdout and json.loads(response.stdout)["outcome"] == "failed" and
              TRANSFER_ONLY_NOT_STORE_FILES_NOT_FOUND_VERIFICATION in
              json.loads(response.stdout)["failure-description"]):
            log.logger.debug("TRANSFER_ONLY_NOT_STORE_FILES system property not found on "
                             "push service({0})".format(self.push_service_ip))
            return "FALSE"
        else:
            raise EnvironError("Unable to get TRANSFER_ONLY_NOT_STORE_FILES value from "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def get_use_dummy_ccpdservice_mo_configured_value(self):
        """
        Get the USE_DUMMY_CCPDSERVICE_MO configured value from push service.

        :return: USE_DUMMY_CCPDSERVICE_MO value
        :rtype: str
        :raises EnvironError: Unable to get USE_DUMMY_CCPDSERVICE_MO value from push service
        """
        log.logger.debug("Attempt to get the USE_DUMMY_CCPDSERVICE_MO configured value")
        command = GET_USE_DUMMY_CCPDSERVICE_MO_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)
        if (response.rc == 0 and response.stdout and json.loads(response.stdout)["outcome"] == "success" and
                "result" in json.loads(response.stdout) and "value" in json.loads(response.stdout)["result"]):
            return json.loads(response.stdout)["result"]["value"]
        elif (response.rc == 1 and response.stdout and json.loads(response.stdout)["outcome"] == "failed" and
              USE_DUMMY_CCPDSERVICE_MO_NOT_FOUND_VERIFICATION in
              json.loads(response.stdout)["failure-description"]):
            log.logger.debug("USE_DUMMY_CCPDSERVICE_MO system property not found on "
                             "push service({0})".format(self.push_service_ip))
            return "FALSE"
        else:
            raise EnvironError("Unable to get USE_DUMMY_CCPDSERVICE_MO value from "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def add_disable_pushservice_randomtime_value(self, action):
        """
        Add DISABLE_PUSHSERVICE_RANDOMTIME configured value with True/False on push service.

        :param action: enable, disable
        :type action: str
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to add DISABLE_PUSHSERVICE_RANDOMTIME value with TRUE/FALSE on push service
        """
        log.logger.debug("Attempt to add the DISABLE_PUSHSERVICE_RANDOMTIME with {0} on "
                         "push service({1})".format(action, self.push_service_ip))
        command = ADD_DISABLE_PUSHSERVICE_RANDOMTIME_VALUE_CMD.format("" if self.is_cloud_native else SUDO,
                                                                      action=action)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if (response.rc == 0 and response.stdout and "outcome" in json.loads(response.stdout) and
                json.loads(response.stdout)['outcome'] == "success"):
            log.logger.debug("Successfully added DISABLE_PUSHSERVICE_RANDOMTIME value with {0} on "
                             "push service({1})".format(action, self.push_service_ip))
            return True
        else:
            raise EnvironError("unable to add DISABLE_PUSHSERVICE_RANDOMTIME value with {0} on "
                               "push service({1}) due to {2}".format(action, self.push_service_ip, response.stdout))

    def add_enable_end_point_checking_value(self, action):
        """
        Add ENABLE_END_POINT_CHECKING configured value with True/False on push service.
        :param action: enable, disable
        :type action: str
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to add ENABLE_END_POINT_CHECKING value with TRUE/FALSE on push service
        """
        log.logger.debug("Attempt to add the ENABLE_END_POINT_CHECKING with {0} on "
                         "push service({1})".format(action, self.push_service_ip))
        command = ADD_ENABLE_END_POINT_CHECKING_VALUE_CMD.format("" if self.is_cloud_native else SUDO, action=action)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if (response.rc == 0 and response.stdout and "outcome" in json.loads(response.stdout) and
                json.loads(response.stdout)['outcome'] == "success"):
            log.logger.debug("Successfully added ENABLE_END_POINT_CHECKING value with {0} on "
                             "push service({1})".format(action, self.push_service_ip))
            return True
        else:
            raise EnvironError("unable to add ENABLE_END_POINT_CHECKING value with {0} on "
                               "push service({1}) due to {2}".format(action, self.push_service_ip, response.stdout))

    def add_transfer_only_not_store_files_value(self, action):
        """
        Add TRANSFER_ONLY_NOT_STORE_FILES configured value with True/False on push service.

        :param action: enable, disable
        :type action: str
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to add TRANSFER_ONLY_NOT_STORE_FILES value with TRUE/FALSE on push service
        """
        log.logger.debug("Attempt to add the TRANSFER_ONLY_NOT_STORE_FILES with {0} on "
                         "push service({1})".format(action, self.push_service_ip))
        command = ADD_TRANSFER_ONLY_NOT_STORE_FILES_VALUE_CMD.format("" if self.is_cloud_native else SUDO,
                                                                     action=action)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)
        if (response.rc == 0 and response.stdout and "outcome" in json.loads(response.stdout) and
                json.loads(response.stdout)['outcome'] == "success"):
            log.logger.debug("Successfully added TRANSFER_ONLY_NOT_STORE_FILES value with {0} on "
                             "push service({1})".format(action, self.push_service_ip))
            return True
        else:
            raise EnvironError("unable to add TRANSFER_ONLY_NOT_STORE_FILES value with {0} on "
                               "push service({1}) due to {2}".format(action, self.push_service_ip,
                                                                     response.stdout))

    def add_use_dummy_ccpdservice_mo_value(self, action):
        """
        Add USE_DUMMY_CCPDSERVICE_MO configured value with True/False on push service.

        :param action: enable, disable
        :type action: str
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to add USE_DUMMY_CCPDSERVICE_MO value with TRUE/FALSE on push service
        """
        log.logger.debug("Attempt to add the USE_DUMMY_CCPDSERVICE_MO with {0} on "
                         "push service({1})".format(action, self.push_service_ip))
        command = ADD_USE_DUMMY_CCPDSERVICE_MO_CMD.format("" if self.is_cloud_native else SUDO, action=action)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if (response.rc == 0 and response.stdout and "outcome" in json.loads(response.stdout) and
                json.loads(response.stdout)['outcome'] == "success"):
            log.logger.debug("Successfully added USE_DUMMY_CCPDSERVICE_MO value with {0} on "
                             "push service({1})".format(action, self.push_service_ip))
            return True
        else:
            raise EnvironError("Unable to add USE_DUMMY_CCPDSERVICE_MO value with {0} on "
                               "push service({1}) due to {2}".format(action, self.push_service_ip,
                                                                     response.stdout))

    def remove_disable_pushservice_randomtime_property_on_push_service_sg(self):
        """
        Remove DISABLE_PUSHSERVICE_RANDOMTIME property on push service SG
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to remove DISABLE_PUSHSERVICE_RANDOMTIME property on push service
        """
        log.logger.debug("Attempt to remove the DISABLE_PUSHSERVICE_RANDOMTIME property on "
                         "push service({0})".format(self.push_service_ip))
        command = REMOVE_DISABLE_PUSHSERVICE_RANDOMTIME_PROPERTY_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if response.rc == 0 and response.stdout and json.loads(response.stdout)['outcome'] == "success":
            log.logger.debug("Successfully removed DISABLE_PUSHSERVICE_RANDOMTIME property on "
                             "push service({0})".format(self.push_service_ip))
            return True
        elif response.rc == 1 and response.stdout and (json.loads(response.stdout)["outcome"] == "failed" and
                                                       DISABLE_PUSHSERVICE_RANDOMTIME_NOT_FOUND_VERIFICATION in
                                                       json.loads(response.stdout)["failure-description"]):
            log.logger.debug("DISABLE_PUSHSERVICE_RANDOMTIME system property not existed on "
                             "push service({0})".format(self.push_service_ip))
            return True
        else:
            raise EnvironError("Unable to remove DISABLE_PUSHSERVICE_RANDOMTIME property on "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def remove_enable_end_point_checking_property_on_push_service_sg(self):
        """
        Remove ENABLE_END_POINT_CHECKING property on push service SG
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to remove ENABLE_END_POINT_CHECKING property on push service
        """
        log.logger.debug("Attempt to remove the ENABLE_END_POINT_CHECKING property on "
                         "push service({0})".format(self.push_service_ip))
        command = REMOVE_ENABLE_END_POINT_CHECKING_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)

        if response.rc == 0 and response.stdout and json.loads(response.stdout)['outcome'] == "success":
            log.logger.debug("Successfully removed ENABLE_END_POINT_CHECKING property on "
                             "push service({0})".format(self.push_service_ip))
            return True
        elif response.rc == 1 and response.stdout and (json.loads(response.stdout)["outcome"] == "failed" and
                                                       ENABLE_END_POINT_CHECKING_NOT_FOUND_VERIFICATION in
                                                       json.loads(response.stdout)["failure-description"]):
            log.logger.debug("ENABLE_END_POINT_CHECKING system property not existed on "
                             "push service({0})".format(self.push_service_ip))
            return True
        else:
            raise EnvironError("Unable to remove ENABLE_END_POINT_CHECKING property on "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def remove_use_dummy_ccpdservice_mo_property_on_push_service_sg(self):
        """
        Remove USE_DUMMY_CCPDSERVICE_MO property on push service SG
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to remove USE_DUMMY_CCPDSERVICE_MO property on push service
        """
        log.logger.debug("Attempt to remove the USE_DUMMY_CCPDSERVICE_MO property on "
                         "push service({0})".format(self.push_service_ip))
        command = REMOVE_USE_DUMMY_CCPDSERVICE_MO_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)
        if response.rc == 0 and response.stdout and json.loads(response.stdout)['outcome'] == "success":
            log.logger.debug("Successfully removed USE_DUMMY_CCPDSERVICE_MO property on "
                             "push service({0})".format(self.push_service_ip))
            return True
        elif response.rc == 1 and response.stdout and (json.loads(response.stdout)["outcome"] == "failed" and
                                                       USE_DUMMY_CCPDSERVICE_MO_NOT_FOUND_VERIFICATION in
                                                       json.loads(response.stdout)["failure-description"]):
            log.logger.debug("USE_DUMMY_CCPDSERVICE_MO system property not existed on "
                             "push service({0})".format(self.push_service_ip))
            return True
        else:
            raise EnvironError("Unable to remove USE_DUMMY_CCPDSERVICE_MO property on "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def remove_transfer_only_not_store_files_property_on_push_service_sg(self):
        """
        Remove TRANSFER_ONLY_NOT_STORE_FILES property on push service SG
        :return: Boolean to indicate success of operation
        :rtype: bool
        :raises EnvironError: Unable to remove TRANSFER_ONLY_NOT_STORE_FILES property on push service
        """
        log.logger.debug("Attempt to remove the TRANSFER_ONLY_NOT_STORE_FILES property on "
                         "push service({0})".format(self.push_service_ip))
        command = REMOVE_TRANSFER_ONLY_NOT_STORE_FILES_CMD.format("" if self.is_cloud_native else SUDO)
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, command)
            response = shell.run_local_cmd(cmd)
        else:
            response = shell.run_cmd_on_vm(shell.Command(command), vm_host=self.push_service_ip)
        if response.rc == 0 and response.stdout and json.loads(response.stdout)['outcome'] == "success":
            log.logger.debug("Successfully removed TRANSFER_ONLY_NOT_STORE_FILES property on "
                             "push service({0})".format(self.push_service_ip))
            return True
        elif response.rc == 1 and response.stdout and (json.loads(response.stdout)["outcome"] == "failed" and
                                                       TRANSFER_ONLY_NOT_STORE_FILES_NOT_FOUND_VERIFICATION in
                                                       json.loads(response.stdout)["failure-description"]):
            log.logger.debug("TRANSFER_ONLY_NOT_STORE_FILES system property not existed on "
                             "push service({0})".format(self.push_service_ip))
            return True
        else:
            raise EnvironError("Unable to remove TRANSFER_ONLY_NOT_STORE_FILES property on "
                               "push service({0}) due to {1}".format(self.push_service_ip, response.stdout))

    def set_fntpushebsfiles_pib_active(self):
        """
        Update fntPushEbsFilesActive PIB on push service SG
        :raises EnvironError: Unable to Update fntPushEbsFilesActive PIB on push service SG
        """
        try:
            log.logger.debug("Attempt to update the fntPushEbsFilesActive pib on "
                             "push service({0})".format(self.push_service_ip))
            state = get_pib_value_on_enm(enm_service_name='pushservice', pib_parameter_name='fntPushEbsFilesActive')
            if str(state).lower() != 'ebsn_du,ebsn_cuup,ebsn_cucp':
                log.logger.debug("Pib parameter fntPushEbsFilesActive is not set, so enabling the pib parameter")
                update_pib_parameter_on_enm(enm_service_name='pushservice',
                                            pib_parameter_name='fntPushEbsFilesActive',
                                            pib_parameter_value='EBSN_DU,EBSN_CUUP,EBSN_CUCP')
                log.logger.debug("Setting fntPushEbsFilesActive PIB parameter complete")
        except Exception as e:
            raise EnvironError("Unable to update the fntPushEbsFilesActive pib due to {0}".format(e))

    def disable_random_time_on_push_service(self):
        """
        This method performs the following operations like i.e.;
        get DISABLE_PUSHSERVICE_RANDOMTIME configured value,
        remove DISABLE_PUSHSERVICE_RANDOMTIME property on push service sg,
        add DISABLE_PUSHSERVICE_RANDOMTIME value.

        :return: Boolean to indicate success of operation
        :rtype: bool
        """
        disable_pushservice_randomtime_value = self.get_disable_pushservice_randomtime_configured_value()
        log.logger.debug("DISABLE_PUSHSERVICE_RANDOMTIME value : {0}".format(disable_pushservice_randomtime_value))
        value = True if disable_pushservice_randomtime_value == "TRUE" else False
        if not value:
            if self.remove_disable_pushservice_randomtime_property_on_push_service_sg():
                return self.add_disable_pushservice_randomtime_value("TRUE")
        else:
            log.logger.debug("Already Random Time is disabled on Push service({0})".format(self.push_service_ip))
            return True

    def disable_end_point_checking_on_push_service(self):
        """
        This method performs the following operations like i.e.;
        get ENABLE_END_POINT_CHECKING configured value,
        remove ENABLE_END_POINT_CHECKING property on push service sg,
        add ENABLE_END_POINT_CHECKING time value.

        :return: Boolean to indicate success of operation
        :rtype: bool
        """
        enable_end_point_checking_value = self.get_enable_end_point_checking_configured_value()
        log.logger.debug("ENABLE_END_POINT_CHECKING_CMD value : {0}".format(enable_end_point_checking_value))
        value = True if enable_end_point_checking_value == "TRUE" else False
        if not value:
            if self.remove_enable_end_point_checking_property_on_push_service_sg():
                return self.add_enable_end_point_checking_value("FALSE")
        else:
            log.logger.debug("Already End Point Checking is disabled on Push service({0})".format(
                self.push_service_ip))
            return True

    def enable_transfer_only_not_store_files_on_push_service(self):
        """
        This method performs the following operations like i.e.;
        get TRANSFER_ONLY_NOT_STORE_FILES configured value,
        remove TRANSFER_ONLY_NOT_STORE_FILES property on push service sg,
        add TRANSFER_ONLY_NOT_STORE_FILES value.

        :return: Boolean to indicate success of operation
        :rtype: bool
        """
        transfer_only_not_store_files_value = self.get_transfer_only_not_store_files_value()
        log.logger.debug("TRANSFER_ONLY_NOT_STORE_FILES value : {0}".format(transfer_only_not_store_files_value))
        value = True if transfer_only_not_store_files_value == "TRUE" else False
        if not value:
            if self.remove_transfer_only_not_store_files_property_on_push_service_sg():
                return self.add_transfer_only_not_store_files_value("TRUE")
        else:
            log.logger.debug("Already Transfer to /dev/null is enabled on Push service({0})".format(
                self.push_service_ip))
            return True

    def enable_use_dummy_ccpdservice_mo_on_push_service(self):
        """
        This method performs the following operations like i.e.;
        get USE_DUMMY_CCPDSERVICE_MO configured value,
        remove USE_DUMMY_CCPDSERVICE_MO property on push service sg,
        add USE_DUMMY_CCPDSERVICE_MO with TRUE value.

        :return: Boolean to indicate success of operation
        :rtype: bool
        """
        use_dummy_ccpdservice_mo_value = self.get_use_dummy_ccpdservice_mo_configured_value()
        log.logger.debug("USE_DUMMY_CCPDSERVICE_MO value : {0}".format(use_dummy_ccpdservice_mo_value))
        value = True if use_dummy_ccpdservice_mo_value == "TRUE" else False
        if not value:
            if self.remove_use_dummy_ccpdservice_mo_property_on_push_service_sg():
                return self.add_use_dummy_ccpdservice_mo_value("TRUE")
        else:
            log.logger.debug("Already USE_DUMMY_CCPDSERVICE_MO value is enabled on Push service({0})".format(
                self.push_service_ip))
            return True

    def execute_tasks(self):
        """
        This method performs the following operations like i.e. Enable push file transfer service, teardown operations.
        """
        self.teardown_list.append(partial(picklable_boundmethod(self.ftpes_setup_on_vm_teardown)))
        self.teardown_list.append(partial(
            picklable_boundmethod(self.remove_disable_pushservice_randomtime_property_on_push_service_sg)))
        self.teardown_list.append(partial(
            picklable_boundmethod(self.remove_enable_end_point_checking_property_on_push_service_sg)))
        self.teardown_list.append(partial(
            picklable_boundmethod(self.remove_transfer_only_not_store_files_property_on_push_service_sg)))
        self.teardown_list.append(partial(
            picklable_boundmethod(self.remove_use_dummy_ccpdservice_mo_property_on_push_service_sg)))
        self.teardown_list.append(partial(
            update_pib_parameter_on_enm, enm_service_name='pushservice',
            pib_parameter_name='fntPushEbsFilesActive', pib_parameter_value='None'))
        self.teardown_list.append(partial(
            picklable_boundmethod(self.enable_and_disable_push_file_transfer_service), "disable"))

        push_file_transfer_status = self.get_status_of_push_file_transfer()
        if push_file_transfer_status:
            if "Product Data: Disabled" in push_file_transfer_status:
                self.enable_and_disable_push_file_transfer_service("enable")
            elif "Product Data: Disabling" in push_file_transfer_status:
                self.wait_product_data_to_enable_disable_state("Disabled")
                self.enable_and_disable_push_file_transfer_service("enable")

    def wait_product_data_to_enable_disable_state(self, state):
        """
        wait and checks for product data to become 'Enabled' or 'Disabled'

        :type state: str
        :param state: state of product data. Enabled or Disabled
        :rtype: bool
        :return: returns True, if Product Data is Enabled or Disabled.

        :raises EnvironError: when Product Data is not enabled/disabled, after expire time
        """
        log.logger.debug("Checking the product data status")
        sleep_time = (SLEEP_TIME_TO_VERIFY_THE_PRODUCT_DATA_ENABLED_STATUS if state == "Enabled" else
                      SLEEP_TIME_TO_VERIFY_THE_PRODUCT_DATA_DISABLED_STATUS)
        expiry_time = datetime.datetime.now() + datetime.timedelta(
            seconds=(EXPIRY_TIME_TO_VERIFY_THE_PRODUCT_DATA_ENABLE_STATUS if state == "Enabled" else
                     EXPIRY_TIME_TO_VERIFY_THE_PRODUCT_DATA_DISABLE_STATUS))
        while datetime.datetime.now() < expiry_time:
            response = self.get_status_of_push_file_transfer()
            log.logger.debug("Desired state: {0}, response of product data: {1}".format(state, response))
            if response and "Product Data: {0}".format(state) in response:
                log.logger.debug("Successfully Product Data is {0}: {1}".format(state, response))
                return True
            log.logger.debug("Product Data is still in {0} state, Sleeping for {1} seconds before "
                             "re-trying..".format(("enabling" if state == "Enabled" else "disabling"),
                                                  sleep_time))
            time.sleep(sleep_time)
        raise EnvironError("Product Data is not {0}, after {1} seconds".format(
            state, (EXPIRY_TIME_TO_VERIFY_THE_PRODUCT_DATA_ENABLE_STATUS if state == "Enabled" else
                    EXPIRY_TIME_TO_VERIFY_THE_PRODUCT_DATA_DISABLE_STATUS)))

    def get_vault_token_from_push_service(self):
        """
        Get value token from push service vm/pod.

        :rtype: object
        :return: returns the pushservice vault_token object.

        :raises EnvironError: Unable to get vault token from push service vm/pod.
        """
        if self.is_cloud_native:
            cmd = KUBECTL_CMD.format(self.cenm_namespace, self.push_service_ip, GET_VAULT_TOKEN_CMD)
            vault_token = shell.run_local_cmd(cmd)
        else:
            vault_token = shell.run_cmd_on_vm(shell.Command(GET_VAULT_TOKEN_CMD), vm_host=self.push_service_ip)

        if not vault_token.ok:
            raise EnvironError("Unable to get vault token from pushservice due to {0}".format(vault_token.stdout))
        log.logger.debug("Vault Token:{0}".format(vault_token.stdout))
        return vault_token

    def create_pushservice_privateKey_file_on_push_service(self):
        """
        Create PushService_PrivateKey.json file (/tmp/PushService_PrivateKey.json) on push service vm/pod.

        :rtype: object
        :return: returns the create_private_key_json_file_on_pushservice_vm response object.

        :raises EnvironError: Unable to create PushService_PrivateKey.json file on pushservice vm/pod.
        """
        private_key_json_file_path = get_internal_file_path_for_import("etc", "pm_49_ftpes_setup_files",
                                                                       "PushService_PrivateKey.json")
        if self.is_cloud_native:
            cmd = ('/usr/local/bin/kubectl --kubeconfig /root/.kube/config cp {0} {1}/{2}:{3} '
                   '2>/dev/null'.format(private_key_json_file_path, self.cenm_namespace,
                                        self.push_service_ip, "/tmp/"))
            create_private_key_json_file_on_pushservice_vm = shell.run_local_cmd(cmd)
        else:
            private_key_data = open(private_key_json_file_path, 'rb').read()
            create_private_key_json_file_cmd = "echo '{}' > /tmp/PushService_PrivateKey.json"
            create_private_key_json_file_on_pushservice_vm = shell.run_cmd_on_vm(shell.Command(
                create_private_key_json_file_cmd.format(private_key_data)), vm_host=self.push_service_ip)

        if not create_private_key_json_file_on_pushservice_vm.ok:
            raise EnvironError("Unable to create PushService_PrivateKey.json file in pushservice "
                               "due to {0}".format(create_private_key_json_file_on_pushservice_vm.stdout))

        return create_private_key_json_file_on_pushservice_vm

    def post_private_key_to_vault_on_pushservice(self, vault_token):
        """
        Post private key to vault on push service vm/pod.

        :type vault_token: object
        :param vault_token: vault_token response object.

        :rtype: object
        :return: returns the post_private_key_to_vault response object.

        :raises EnvironError: Unable to post private key to vault on push service vm/pod.
        """
        post_private_key_to_vault_cmd = POST_GENERATAED_KEY_USING_VAULT_TOKEN.format(token=vault_token.stdout)
        if self.is_cloud_native:
            kubectl_cmd = ('''/usr/local/bin/kubectl --kubeconfig /root/.kube/config exec -n {0} {1} -c pushservice -- bash -c '{2}' 2>/dev/null''')
            cmd = kubectl_cmd.format(self.cenm_namespace, self.push_service_ip, post_private_key_to_vault_cmd)
            post_private_key_to_vault = shell.run_local_cmd(cmd)
        else:
            post_private_key_to_vault = shell.run_cmd_on_vm(shell.Command(post_private_key_to_vault_cmd),
                                                            vm_host=self.push_service_ip)
        if not post_private_key_to_vault.ok:
            raise EnvironError("Unable to post private key to vault on pushservice "
                               "due to {0}".format(post_private_key_to_vault.stdout))
        return post_private_key_to_vault
