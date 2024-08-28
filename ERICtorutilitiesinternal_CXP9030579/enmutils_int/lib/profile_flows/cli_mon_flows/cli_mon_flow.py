from enmutils.lib import log
from enmutils.lib.exceptions import ShellCommandReturnedNonZero, EnmApplicationError
from enmutils.lib.shell import Command, run_local_cmd, run_cmd_on_ms, run_cmd_on_cloud_native_pod
from enmutils.lib.cache import (is_enm_on_cloud_native, get_enm_cloud_native_namespace)
from enmutils_int.lib.enm_deployment import get_pod_hostnames_in_cloud_native
from enmutils_int.lib.common_utils import check_for_active_litp_plan
from enmutils_int.lib.profile_flows.common_flows.common_flow import FlowProfile


class CliMon01Flow(FlowProfile):

    ENMINST_SYSTEM_HEALTHCHECK_COMMAND = '/opt/ericsson/enminst/bin/enm_healthcheck.sh -v'
    cENM_SYSTEM_HEALTHCHECK_COMMAND = 'kubectl exec -it {0} -n {1} -- enm_hc -v'

    PRE_ERROR_MESSAGE = "ENM System Health command output did not contain"
    ENMINST_SUCCESS_MESSAGE = "Successfully Completed ENM System Healthcheck"
    cENM_FAILURE_MESSAGE = "Health check failed."
    POST_ERROR_MESSAGE = " - See profile log file for more details"

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"
        while self.keep_running():
            try:
                if is_enm_on_cloud_native():
                    self.verify_health_check_response_on_cloud_native()
                else:
                    self.verify_health_check_response()
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    def execute_system_health_check(self):
        """
        Connect to MS and run ENMINST_SYSTEM_HEALTHCHECK script in verbose mode - store output in a temp file
        Note: get_pty=True required as workaround for TORF-151381 (i.e. using pseudo-tty in SSH connection)

        :return: List containing the response delimited by new line
        :rtype: list
        """
        command_response = run_cmd_on_ms(Command("{enminst_cmd}".format(
            enminst_cmd=self.ENMINST_SYSTEM_HEALTHCHECK_COMMAND), timeout=600), get_pty=True)
        return command_response.stdout.split("\n")

    def verify_health_check_response_on_cloud_native(self):
        """
        If the lines of output contains the cENM_SUCCESS_MESSAGE,
        then the ENM health check didn't encounter problems on the system
        """
        pod_name = get_pod_hostnames_in_cloud_native('troubleshooting-utils')[0]
        response = run_cmd_on_cloud_native_pod('troubleshooting-utils', pod_name,
                                               self.cENM_SYSTEM_HEALTHCHECK_COMMAND.format(
                                                   pod_name, get_enm_cloud_native_namespace()))
        response_lines = response.stdout.split("\n")
        health_check_successful = False
        for line in response_lines[:]:
            if self.cENM_FAILURE_MESSAGE in line:
                health_check_successful = False
                break
            else:
                health_check_successful = True
        # Report problem via profile
        if not health_check_successful:
            profile_error_message = 'ENM System Health Check Failed - See profile log file for more details'
            self.add_error_as_exception(EnmApplicationError(profile_error_message))

    def verify_health_check_response(self):
        """
        If the last 5 lines of output contains the ENMINST_SUCCESS_MESSAGE,
        then the ENM health check didn't encounter problems on the system
        """
        if check_for_active_litp_plan():
            log.logger.debug("Unable to execute ENM Health Check, active litp plan detected.")
            return
        response_lines = self.execute_system_health_check()
        health_check_successful = False
        for line in response_lines[-5:]:
            if self.ENMINST_SUCCESS_MESSAGE in line:
                health_check_successful = True
                break
        # Report problem via profile
        if not health_check_successful:
            profile_error_message = "{0} '{1}' {2}".format(self.PRE_ERROR_MESSAGE,
                                                           self.ENMINST_SUCCESS_MESSAGE,
                                                           self.POST_ERROR_MESSAGE)
            self.add_error_as_exception(EnmApplicationError(profile_error_message))


class CliMon03Flow(FlowProfile):

    ENM_CLI_COMMAND = '/opt/ericsson/enmutils/bin/cli_app "cmedit get * CmFunction.syncStatus"'

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"

        while self.keep_running():
            try:
                command_response = run_local_cmd(Command(self.ENM_CLI_COMMAND, timeout=60 * 10))
                if command_response.rc != 0:
                    raise ShellCommandReturnedNonZero("{0}".format(command_response.stdout), command_response)
            except Exception as e:
                self.add_error_as_exception(e)

            self.sleep()
