from os.path import join

import time
import pexpect

from enmutils.lib import log, filesystem, config
from enmutils.lib.kubectl_commands import EXECUTE_AMOS_SCRIPT
from enmutils.lib.cache import (CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM,
                                get_emp, get_ms_host, is_emp,
                                is_enm_on_cloud_native, get_enm_cloud_native_namespace)
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.shell import (DEFAULT_VM_SSH_KEYPATH, Command,
                                copy_file_between_wlvm_and_cloud_native_pod,
                                run_cmd_on_cloud_native_pod, run_cmd_on_ms,
                                run_cmd_on_vm, run_local_cmd)
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.enm_deployment import get_pod_hostnames_in_cloud_native
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_list_of_scripting_service_ips


class AmosFlow(FlowProfile):
    AMOS_LOGS_CRONJOB = "AMOS_LOGS_CRONJOB.txt"
    key_location = ""
    AMOS_LOG_CLEANUP_SCRIPT = "/ericsson/ERICamosservice2_CXP9039087/scripts/amos_log_cleanup_scheduler.sh"
    NO_HOST_CHECK = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    ROOT_USER = "root"
    USER = "cloud-user"
    PASSWORD = "passw0rd"
    SRCDIR = "/var/tmp/"
    DSTDIR = "/home/cloud-user"
    CRONFILE = "/etc/cron.d/AMOS_LOGS_CRONJOB"

    def get_scripting_vms_ips(self):
        """
        Returns all Scripting VMs ip/pods names addresses on ENM deployment

        return: A list with all Scripting cluster ips in ENM deployment
        rtype: list
        """
        log.logger.debug("Fetching scripting vms ips")
        if self.IS_CLOUD_NATIVE:
            scripting_cluster_ips = get_pod_hostnames_in_cloud_native('general-scripting')
        else:
            scripting_cluster_ips = get_list_of_scripting_service_ips()
        log.logger.debug("scripting cluster ips: {0}".format(scripting_cluster_ips))
        return scripting_cluster_ips

    def adjust_minute_field_in_amos_logs_cronjob_file_per_vm(self, crontab_minute):
        """
        Adjust the minute field in the cron schedule so that execution on one VM does not interfere
        with execution on another, as /ericsson/log/amos is a shared file system.
        For example: If you run on scp-1-amos at minute 0, run on scp-2-amos at minute 5.

        :type crontab_minute: int
        :param crontab_minute: adjust the minute field on the amos logs crontab file with this value
        :raises EnvironError: if file permissions cannot be changed

        """
        log.logger.debug("Attempt to adjust the minute field in amos logs cronjob file")
        try:
            file_path = get_internal_file_path_for_import("etc", "data", self.AMOS_LOGS_CRONJOB)
            cmd = Command("cp {0} {1}".format(file_path, self.SRCDIR), timeout=60 * 1)
            cmd_response = run_local_cmd(cmd)
            if cmd_response.rc != 0:
                raise Exception("Failed to copy AMOS logs file to /var/tmp on workload vm.")
            log.logger.info("AMOS logs cronjob is copied to {0} on workload vm for adjustment of crontab minute "
                            "field".format(self.SRCDIR))
            cronjob_path = join(self.SRCDIR, self.AMOS_LOGS_CRONJOB)
            with open(cronjob_path, "r") as f:
                content = f.read().replace('23', str(crontab_minute[0])).replace('00', str(crontab_minute[1]))
                log.logger.debug("{}".format(content))

            with open(cronjob_path, 'w') as f:
                f.write(content)
                log.logger.debug("{}".format(content))

            log.logger.debug("Adjusted the amos crontab file by 5 minutes")
        except Exception as e:
            raise EnvironError("Exception: {0}".format(e.message))

    def transfer_amos_logs_cron_job_from_workload_vm(self, scripting_cluster_ip=None):
        """
        It copies the amos logs cronjob file from workload vm onto EMP/MS/scripting server

        :raises Exception: if files cannot be transferred from the workload vm
        :raises EnvironError: if command execution to transfer AMOS logs cronjob file fails
        """
        log.logger.debug("Attempt to transfer the amos logs cron job from workload vm")
        try:
            if self.IS_EMP:
                cmd = "scp -i {0} {1}{2} {3}@{4}:{5}".format(CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, self.SRCDIR,
                                                             self.AMOS_LOGS_CRONJOB, self.USER, get_emp(), self.SRCDIR)
                cmd_response = run_local_cmd(Command(cmd, timeout=60 * 1))
            elif self.IS_CLOUD_NATIVE:
                cmd_response = copy_file_between_wlvm_and_cloud_native_pod(scripting_cluster_ip, "{0}{1}".format(
                    self.SRCDIR, self.AMOS_LOGS_CRONJOB), self.SRCDIR, 'to')
            else:
                cmd = "scp {0}/{1} {2}@{3}:{4}".format(self.SRCDIR, self.AMOS_LOGS_CRONJOB, self.ROOT_USER, get_ms_host(),
                                                       self.SRCDIR)
                cmd_response = run_local_cmd(Command(cmd, timeout=60 * 1))
            if cmd_response.rc != 0:
                raise Exception("Failed to transfer AMOS logs cronjob from Workload VM to emp/MS/scripting server."
                                " Response : {0}".format(cmd_response.stdout))
            log.logger.info("AMOS logs cronjob is transferred to {0} on emp/MS/scripting server".format(self.SRCDIR))
        except Exception as e:
            raise EnvironError("Exception: {0}".format(e.message))

    def copy_amos_cron_job_into_cron_folder(self, host):
        """
        Log onto VM with root user & copy file from /home/cloud-user to /etc/cron.d for cronjob to scan and pick up

        :type host: str
        :param host: IP address of the amos/scripting cluster vm on which the command is to be executed
        :raises EnvironError: if cron file cannot be moved to '/etc/cron.d' crontab file directory
        """
        log.logger.debug("Attempt to copy the amos cron job into cron folder")
        try:
            cmd = "sudo scp {0}/{1} {2}".format(self.DSTDIR, self.AMOS_LOGS_CRONJOB, self.CRONFILE)
            if self.IS_CLOUD_NATIVE:
                cmd = "cp {0}/{1} {2}".format(self.DSTDIR, self.AMOS_LOGS_CRONJOB, self.CRONFILE)
                command_response = run_cmd_on_cloud_native_pod("general-scripting", host, cmd)
            else:
                command_response = run_cmd_on_vm(cmd, host)
            if command_response.rc != 0:
                raise Exception("Failed to copy amos logs crontab file to crontab file directory "
                                "/etc/cron.d {0}".format(command_response.stdout), command_response)
            log.logger.debug("Copied amos crontab file to {0}".format(self.CRONFILE))
        except Exception as e:
            raise EnvironError("Exception: {0}".format(e.message))

    def change_cron_job_file_permissions(self, host):
        """
        Log onto VM with root user & change file permissions of the file present in /etc/cron.d

        :type host: str
        :param host: IP address of the amos/scripting cluster vm on which the command is to be executed
        :raises EnvironError: if cron file cannot be moved to '/etc/cron.d' crontab file directory
        """
        log.logger.debug("Attempt to change the cron job file permissions")
        try:
            cmd = "sudo chmod 644 {0}".format(self.CRONFILE)
            if self.IS_CLOUD_NATIVE:
                cmd = "chmod 644 {0}".format(self.CRONFILE)
                command_response = run_cmd_on_cloud_native_pod("general-scripting", host, cmd)
            else:
                command_response = run_cmd_on_vm(cmd, host)
            if command_response.rc != 0:
                raise Exception("Failed to change file permissions of amos logs crontab file {0}".format(
                    command_response.stdout), command_response)
            log.logger.debug("Changed {0} permissions to 644.".format(self.CRONFILE))
        except Exception as e:
            raise EnvironError("Exception: {0}".format(e.message))

    def transfer_amos_logs_cron_job_to_scripting_vms(self, host):
        """
        Copy amos crontab file up to /home/cloud-user directory in scripting VMs/pods

        :type host: str
        :param host: IP address of the amos/scripting cluster vm on which the command is to be executed
        :raises EnvironError: if it cannot ssh to the physical/cloud vms from ms/emp
        """
        log.logger.debug("Attempt to transfer the amos logs cron job to scripting vms")
        try:
            if self.IS_EMP:
                cmd = "scp -i {0} -o stricthostkeychecking=no {1}{2} {3}@{4}:{5}".format(
                    CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP, self.SRCDIR, self.AMOS_LOGS_CRONJOB, self.USER, host,
                    self.DSTDIR)
                command_response = run_cmd_on_vm(cmd, get_emp())
            elif self.IS_CLOUD_NATIVE:
                command_response = copy_file_between_wlvm_and_cloud_native_pod(host, "{0}{1}".format(
                    self.SRCDIR, self.AMOS_LOGS_CRONJOB), self.DSTDIR, 'to')
            else:
                cmd = "scp -i {0} -o stricthostkeychecking=no {1}{2} {3}@{4}:{5}".format(DEFAULT_VM_SSH_KEYPATH,
                                                                                         self.SRCDIR,
                                                                                         self.AMOS_LOGS_CRONJOB,
                                                                                         self.USER, host, self.DSTDIR)
                command_response = run_cmd_on_ms(cmd)

            if command_response.rc != 0:
                raise Exception("Failed to SSH onto amos/scripting vm {0}. {1}".format(host, command_response.stdout),
                                command_response)
            log.logger.info("The crontab file to clear AMOS logs is copied up to {0}".format(host))
        except Exception as e:
            raise EnvironError("Exception: {0}".format(e.message))

    def set_key_location(self):
        """
        Sets the key location based on whether it is on cloud or physical
        """
        if config.is_a_cloud_deployment():
            self.key_location = "/var/tmp/enm_keypair.pem"
        else:
            self.key_location = "/root/.ssh/vm_private_key"
        if not filesystem.does_file_exist(self.key_location):
            self.add_error_as_exception(EnvironError("Cannot find pem key!!"))
            log.logger.debug("Key file not found!!!")

    def amos_log_cleanup_script_cloudnative(self, cmd, scripting_vm):
        """
        Runs the amos_log_cleanup_scheduler.sh in cloud Native deployment in the scripting pod
        :type scripting_vm: str
        :param scripting_vm: IP address of the amos/scripting cluster vm on which the command is to be executed
        :type cmd: str
        :param cmd: Command which is used to login to scripting pod from workload VM
        :raises EnvironError: Cannot reach the desired pod
        :raises EnmApplicationError: when amos_log_cleanup_scheduler.sh fails
        """
        script_failed_message = "Script not executing properly on scp vm because {0} \n Before:{1} \n After:{2}"
        with pexpect.spawn(cmd) as child:
            rc = child.expect(["{0}".format(scripting_vm), pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnvironError("Cannot connect to scripting vm because {0} \n Before:{1} \n After:{2}"
                                   .format(rc, child.before, child.after))
            child.sendline(self.AMOS_LOG_CLEANUP_SCRIPT)
            rc = child.expect(["Enter your choice", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            log.logger.debug("Got Enter your choice first time")
            child.sendline("C")
            rc = child.expect(["Please enter your choice ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("true")
            log.logger.debug("Updated value of C as true")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("R")
            rc = child.expect(["Please enter deletion period for log files/traces created from normal commands",
                               pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("1")
            rc = child.expect(["Please enter deletion period for log files/traces created from heavy commands",
                               pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("1")
            log.logger.debug("Updated value of R as 1")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("S")
            rc = child.expect(["Please enter hour in schedule ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("23")
            rc = child.expect(["Please enter minute in schedule ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("00")
            log.logger.debug("Updated value of S as 23:00")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("Q")
            rc = child.expect(["Cleanup cron for /ericsson/log/amos is enabled", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError("Script execution failed because {0} \n Before:{1} \n After:{2}"
                                          .format(rc, child.before, child.after))
            log.logger.debug("AMOS cleanup script successfully executed")

    def amos_log_cleanup_script_cloud_and_physical(self, scripting_vm):
        """
        Runs the amos_log_cleanup_scheduler.sh in cloud or physical deployment in the scripting vm
        :type scripting_vm: str
        :param scripting_vm: IP address of the amos/scripting cluster vm on which the command is to be executed
        :raises EnvironError: Cannot reach the desired vm or not switched to root user
        :raises EnmApplicationError: when amos_log_cleanup_scheduler.sh fails
        """
        script_failed_message = "Script not executing properly on scp vm because {0} \n Before:{1} \n After:{2}"
        initial_expect = "root@" if not config.is_a_cloud_deployment else "cloud-user@"
        cmd = "ssh -i {0} {1} cloud-user@{2}".format(self.key_location, self.NO_HOST_CHECK, scripting_vm)
        with pexpect.spawn(cmd) as child:
            log.logger.debug("key location: {0}, scripting vm:{1}".format(self.key_location, scripting_vm))
            log.logger.debug("Confirming connection to scripting vm")
            child.sendline("sudo su")
            rc = child.expect([initial_expect, pexpect.EOF])
            if rc != 0:
                raise EnvironError("Not switched to root user because {0} \n Before:{1} \n After:{2}"
                                   .format(rc, child.before, child.after))
            child.sendline(self.AMOS_LOG_CLEANUP_SCRIPT)
            log.logger.debug("Ran AMOS clean script")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("C")
            rc = child.expect(["Please enter your choice ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("true")
            log.logger.debug("Updated value of C as true")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("R")
            rc = child.expect(["Please enter deletion period for log files/traces created from normal commands",
                               pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("1")
            rc = child.expect(["Please enter deletion period for log files/traces created from heavy commands",
                               pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("1")
            log.logger.debug("Updated value of R as 1")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("S")
            rc = child.expect(["Please enter hour in schedule ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("23")
            rc = child.expect(["Please enter minute in schedule ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("00")
            log.logger.debug("Updated value of S as 23:00")
            rc = child.expect(["Enter your choice : ", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError(script_failed_message.format(rc, child.before, child.after))
            child.sendline("Q")
            time.sleep(2)
            rc = child.expect(["Cleanup cron for /ericsson/log/amos is enabled", pexpect.EOF, pexpect.TIMEOUT])
            if rc != 0:
                raise EnmApplicationError("Script execution failed because {0} \n Before:{1} \n After:{2}"
                                          .format(rc, child.before, child.after))
            log.logger.debug("AMOS cleanup script successfully executed")

    def script_execution_amos_log_cleanup(self, scripting_vm):
        """
        Runs amos log clenaup script according to the deployment type
        """
        if self.IS_CLOUD_NATIVE:
            cmd = EXECUTE_AMOS_SCRIPT.format(get_enm_cloud_native_namespace(), scripting_vm)
            self.amos_log_cleanup_script_cloudnative(cmd, scripting_vm)
        else:
            self.set_key_location()
            self.amos_log_cleanup_script_cloud_and_physical(scripting_vm)

    def remove_amos_logs_crontab_file(self):
        """
        Remove amos logs crontab file from EMP/MS and vm/scripting server directory /home/cloud-user
        and crontab directory /etc/cron.d

        :raises Exception: if cron file cannot be moved to '/etc/cron.d' crontab file directory
        """
        log.logger.debug("Attempt to remove the amos logs crontab file")
        cmd = "rm -rf {0}{1}".format(self.SRCDIR, self.AMOS_LOGS_CRONJOB)
        command = "rm -rf {0}/{1}".format(self.DSTDIR, self.AMOS_LOGS_CRONJOB)
        remove_crontab = "sudo rm -rf {0}".format(self.CRONFILE)
        for ip in self.SCRIPTING_CLUSTER_IPS:
            if self.IS_EMP:
                cmd_response = run_local_cmd(Command(cmd, timeout=60 * 1))
                response = run_cmd_on_vm(cmd, get_emp())
                command_response = run_cmd_on_vm(command, ip)
                remove_response = run_cmd_on_vm(remove_crontab, ip)
            elif self.IS_CLOUD_NATIVE:
                cmd_response = run_local_cmd(Command(cmd, timeout=60 * 1))
                command = "rm -rf {0}{1} {2}/{3} {4}".format(self.SRCDIR, self.AMOS_LOGS_CRONJOB, self.DSTDIR,
                                                             self.AMOS_LOGS_CRONJOB, self.CRONFILE)
                remove_response = command_response = response = run_cmd_on_cloud_native_pod("general-scripting", ip,
                                                                                            command)
            else:
                cmd_response = run_local_cmd(Command(cmd, timeout=60 * 1))
                response = run_cmd_on_ms(cmd)
                command_response = run_cmd_on_vm(command, ip)
                remove_response = run_cmd_on_vm(remove_crontab, ip)
            if any([responses.rc != 0 for responses in [cmd_response, command_response, remove_response, response]]):
                raise Exception("Failed to remove AMOS LOGS CRONTAB file from EMP/MS/Scripting server, vm {0}:{1}, "
                                "vm {0}:{2} .".format(ip, self.DSTDIR, self.CRONFILE))

            log.logger.debug("Removed AMOS LOGS CRONTAB file from EMP/MS/Scripting server "
                             "and vm {0} crontab directory /etc/cron.d".format(ip))

    def set_teardown_objects(self, instance_object):
        """
        Add callable objects to the teardown list

        :type instance_object: instance object
        :param instance_object: Add callable class instance objects to the teardown list
        """
        # Remove copies of the cronjob file from WLVM, EMP, MS, amos/scripting vms
        self.teardown_list.append(picklable_boundmethod(instance_object.delete))


class Amos09Flow(AmosFlow):
    SCRIPTING_CLUSTER_IPS = []
    IS_CLOUD_NATIVE = None
    IS_EMP = None

    def execute_flow(self):
        """
        Executes the amos_09 profile flow to enable amos logs housekeeping via cron jobs.
        """

        self.set_teardown_objects(self)
        self.state = "RUNNING"
        self.IS_CLOUD_NATIVE = is_enm_on_cloud_native()
        self.IS_EMP = False if self.IS_CLOUD_NATIVE else is_emp()

        while self.keep_running():
            try:
                self.perform_iteration_actions()
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    def delete(self):
        """
        Add callable objects to the teardown list
        """
        # Remove copies of the cronjob file from WLVM, EMP, MS and both the amos cluster vms and scripting cluster vms
        self.remove_amos_logs_crontab_file()

    def perform_iteration_actions(self):
        """
        This method performs the set of operations such as Get scripting vms ips,
        Adjust the minute field in amos logs cronjob file per vm, Transfer amos logs cron job from workload vm,
        Transfer amos logs cron job to scripting vms, Copy amos cron job into cron folder,
        Change cron job file permissions

        """
        hour_minute = [(23, 30), (0, 0), (00, 30)]
        self.SCRIPTING_CLUSTER_IPS = self.get_scripting_vms_ips()
        for index, ip in enumerate(self.SCRIPTING_CLUSTER_IPS):

            try:
                self.script_execution_amos_log_cleanup(ip)
                self.adjust_minute_field_in_amos_logs_cronjob_file_per_vm(hour_minute[index])
                self.transfer_amos_logs_cron_job_from_workload_vm(ip)
                self.transfer_amos_logs_cron_job_to_scripting_vms(ip)
                self.copy_amos_cron_job_into_cron_folder(ip)
                self.change_cron_job_file_permissions(ip)
            except Exception as e:
                self.add_error_as_exception(e)
                continue
