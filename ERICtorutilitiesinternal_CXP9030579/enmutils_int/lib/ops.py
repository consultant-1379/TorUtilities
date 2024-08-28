# ********************************************************************
# Name    : OPS
# Summary : Used by the OPS profile. Allows the user to set up
#           password-less access to the LMS, check the session count
#           on the OPS vm/pod, and run the WINFIOL script on the vm/pod,
#           responsible for Software management of GSM nodes.
# ********************************************************************

import re
import pexpect

from enmutils.lib import log, shell
from enmutils.lib.cache import is_host_ms, get_ms_host, is_enm_on_cloud_native, get_enm_cloud_native_namespace
from enmutils.lib.exceptions import EnmApplicationError, EnvironError

from enmutils_int.lib import enm_deployment
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_list_of_scripting_service_ips
from enmutils_int.lib.common_utils import get_internal_file_path_for_import


class Ops(object):

    LOAD_SCRIPT_PATH = "/opt/ops/ops_server/utils/bladeRunnerScript/loadScript/OPS_Load_Script_V5.0"
    BLADE_RUNNER_NUI_PATH = "/opt/ops/ops_server/utils/bladeRunnerScript/bladeRunner_NUI.sh"
    BLADE_RUNNER_REST_PATH = "/home/shared/bladeRunner_Rest.sh"
    CHECK_LOG = 'grep -E "Description.*Normal.*program.*termination" {0}/* | wc -l'

    def __init__(self, host_list=None):
        """
        Ops Constructor
        :type host_list: list[strings]
        :param host_list: Addresses of OPS vms/pods in the deployment
        """
        self.is_enm_on_cn = is_enm_on_cloud_native()
        if self.is_enm_on_cn:
            self.host_list = enm_deployment.get_enm_service_locations('ops')
            self.scripting_pod = enm_deployment.get_pod_hostnames_in_cloud_native("general-scripting")[0]
            self.enm_namespace = get_enm_cloud_native_namespace()
        else:
            self.host_list = host_list if host_list else enm_deployment.get_values_from_global_properties("ops=")
        self.scripting_ip = get_list_of_scripting_service_ips()[0]

    def create_password_less_to_vm(self, user, vm):
        """
        Creates passwordless access for the profile user on vm
        :param user: User object to execute commands as
        :type user: `enm_user_2.User`
        :param vm: IP Address of OPS vm
        :type vm: str
        :raises EnvironError: If the ssh-id-copy command fails on emp or ms
        :raises RuntimeError: If the script fails to run
        """
        if self.is_enm_on_cn:
            self.create_password_less_to_vm_cn(user, vm)
        else:
            self.create_password_less_to_vm_penm(user, vm)

    def create_password_less_to_vm_penm(self, user, vm):
        """
        Creates passwordless access for the profile user on vm
        :param user: User object to execute commands as
        :type user: `enm_user_2.User`
        :param vm: IP Address of OPS vm
        :type vm: str
        :raises EnvironError: If the ssh-id-copy command fails on emp or ms
        :raises RuntimeError: If the script fails to run
        """
        if is_host_ms():
            raise RuntimeError("No workload VM detected, exiting profile.")
        msg = "Passwordless access is {0} for {1} user for {2} vm"
        # Verify passwordless access
        cmd = "ssh -o PasswordAuthentication=no -o BatchMode=yes {0}@{1} exit &>/dev/null".format(user.username, vm)
        response = shell.run_remote_cmd(cmd, self.scripting_ip, user.username, user.password)
        if response.rc:
            with pexpect.spawn('ssh -o StrictHostKeyChecking=no root@{0}'.format(get_ms_host())) as child:
                child.expect("root@ieatlms")
                child.sendline("ssh {0}@{1}".format(user.username, self.scripting_ip))
                output = child.expect(['Are you sure you want to continue connecting (yes/no)?', 'password:'])
                if output == 0:
                    child.sendline('yes')
                    child.expect("password:")
                    child.sendline(user.password)
                else:
                    child.sendline(user.password)
                child.expect("scripting")
                child.sendline("ssh-keygen -f $HOME/.ssh/id_rsa -N \'\'")
                child.expect("scripting")
                child.sendline('ssh-copy-id {0}@{1}'.format(user.username, vm))
                output = child.expect(['Are you sure you want to continue connecting (yes/no)?', 'password:'])
                if output == 0:
                    child.sendline('yes')
                    child.expect("password:")
                    child.sendline(user.password)
                else:
                    child.sendline(user.password)
                child.expect("scripting")
                response = shell.run_remote_cmd(cmd, self.scripting_ip, user.username, user.password)
                if response.rc:
                    raise EnvironError(msg.format("not set", user.username, vm))
                else:
                    log.logger.debug(msg.format("set", user.username, vm))
        else:
            log.logger.debug(msg.format("already set", user.username, vm))

    def create_password_less_to_vm_cn(self, user, vm):
        """
        Creates passwordless access for the profile user on vm
        :param user: User object to execute commands as
        :type user: `enm_user_2.User`
        :param vm: IP Address of OPS vm
        :type vm: str
        :raises EnvironError: If the ssh-id-copy command fails on emp or ms
        :raises RuntimeError: If the script fails to run
        """
        msg = "Passwordless access is {0} for {1} user for {2} vm"
        # Verify passwordless access
        cmd = "ssh -o PasswordAuthentication=no -o BatchMode=yes {0}@{1} exit &>/dev/null".format(user.username, vm)
        response = shell.run_remote_cmd(cmd, self.scripting_ip, user.username, user.password)
        if response.rc:
            with pexpect.spawn('kubectl -n {0} exec -it {1} -- bash'.format(self.enm_namespace, self.scripting_pod)) as child:
                child.expect("scripting")
                child.sendline("su {0}".format(user.username))
                child.expect("scripting")
                child.sendline("ssh-keygen -f $HOME/.ssh/id_rsa -N \'\'")
                child.expect("scripting")
                child.sendline('ssh-copy-id {0}@{1}'.format(user.username, vm))
                output = child.expect(['yes/no', 'Password'])
                if output == 0:
                    child.sendline('yes')
                    child.expect("Password")
                    child.sendline(user.password)
                else:
                    child.sendline(user.password)
                child.expect("scripting")
                response = shell.run_remote_cmd(cmd, self.scripting_ip, user.username, user.password)
                if response.rc:
                    raise EnvironError(msg.format("not set", user.username, vm))
                else:
                    log.logger.debug(msg.format("set", user.username, vm))
        else:
            log.logger.debug(msg.format("already set", user.username, vm))

    def copy_bladerunner_rest_script_to_scripting_host(self):
        """
        Copies the bladeRunner_Rest.sh shell script to the scripting host

        :returns: returns the error_msg if script failed to be copied to host
        :rtype: str
        """
        if self.is_enm_on_cn:
            pod_name = enm_deployment.get_enm_service_locations('general-scripting')[0]
            script_path_wlvm = get_internal_file_path_for_import('templates', 'ops', 'bladeRunner_Rest.sh')
            response = shell.copy_file_between_wlvm_and_cloud_native_pod(pod_name, script_path_wlvm,
                                                                         self.BLADE_RUNNER_REST_PATH, 'to')
            if response.rc:
                error_msg = ("Failed to copy the script to {0} on {1}. Profile can't proceed until script is copied to "
                             "the pod. Response-{2}".format(self.BLADE_RUNNER_REST_PATH, pod_name, response.stdout))
                return error_msg
            else:
                log.logger.debug("Script is copied to {0} on {1}".format(self.BLADE_RUNNER_REST_PATH, pod_name))

    def run_blade_runner_script_on_vm(self):
        """ Deprecated in 23.16 and will be deleted in 24.11 RTD-23698 """

    def run_blade_runner_script_on_host(self, user, node_name, host, session_count):
        """
        Runs the blade runner script
        :param user: User object to execute commands as
        :type user: `enm_user_2.User`
        :param node_name: BSC
        :type node_name: str
        :param host: OPS host to run script
        :type host: str
        :param session_count: Number of sessions to be launched for ops
        :type session_count: int
        :raises EnvironError: If the command is not successful on emp or ms
        :raises EnmApplicationError: If the script fails to run
        :return: log file with path
        :rtype: str
        """
        try:
            cmd = ("{BR_script_path} {session_count} {ops_load_script_path} {node_name}"
                   .format(BR_script_path=self.BLADE_RUNNER_NUI_PATH, session_count=session_count,
                           ops_load_script_path=self.LOAD_SCRIPT_PATH, node_name=node_name))
            run_cmd = ('ssh -o StrictHostKeyChecking=no {0}@{1} \"{2}\"'.format(user.username, host, cmd))
            response = shell.run_remote_cmd(run_cmd, self.scripting_ip, user.username, user.password,
                                            **{'timeout': 2000})
        except Exception as e:
            raise EnvironError('Unable to connect to OPS vms/pods. {0}'.format(e.message))
        if response.rc == 0 and 'please check logs at' in response.stdout:
            logfile = response.stdout.split('please check logs at')[1].strip().split(" ")[0].split("\n")[0]
            log.logger.info("Detailed logs can be checked at {0}".format(logfile))
        else:
            raise EnmApplicationError("Error running bladeRunner script {0}: ".format(response.stdout))

        return logfile

    def check_sessions_count(self, user, host, logfile, session_count):
        """
        Checks the number of sessions created by bladeRunner_NUI script
        :param user: User object to execute commands as
        :type user: `enm_user_2.User`
        :param host: OPS host to run script
        :type host: str
        :param session_count: Number of sessions to be launched for ops
        :type session_count: int
        :param logfile: log file from the response of the script
        :type logfile: str
        :raises EnvironError: If the command is not successful on emp or ms
        :raises EnmApplicationError: If the script fails to run
        """
        cmd = ('ssh -o StrictHostKeyChecking=no {0}@{1} \"{2}\"'.format(user, host, self.CHECK_LOG.format(logfile)))
        try:
            response = shell.run_remote_cmd(cmd, self.scripting_ip, user.username, user.password)
        except Exception as e:
            raise EnvironError('Unable to connect to OPS vms/pods. Exception: {0}'.format(e.message))
        if response.rc == 0:
            log.logger.debug("The number of successful ops sessions for {0} are: {1}".format(host, response.stdout))
            res_sout = re.findall(r"\d+", str(response.stdout))
            res_sout = int(res_sout[0]) if res_sout else 0
            log.logger.debug("Total failed ops sessions for {0} are: {1}".format(host, session_count - res_sout))
        else:
            raise EnmApplicationError("Error checking session count from log file {0}: ".format(response.stdout))
