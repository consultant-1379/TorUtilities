import time
import re
from functools import partial
import pexpect
from enmutils.lib import log, cache
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.shell import Command, run_cmd_on_ms
from enmutils_int.lib.common_utils import check_for_active_litp_plan
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow import is_nas_accessible

lms_login_status = "root@ieatlms"
password_format = "[pP]assword:"
nas_login = "ssh  -o StrictHostKeyChecking=no support@nasconsole"
login_msg = ["LOGGED INTO LMS", "LOGGED INTO NAS"]
error_msg = "Problem encountered trying to nas login"
CMD_CONFIG = "./configure_NAS.bsh -a rpm"
CMD_SHOW = "sudo /opt/VRTSnas/clish/bin/clish -u master -c 'cluster show'"
CMD_LOCK = "sudo /opt/VRTSnas/clish/bin/clish -u master -c 'cluster {0} {1}'"
CMD_RESTART = "/sbin/shutdown -r now"
CMD_SUMMARY = "hastatus -summ"
CMD_LMS = "ssh root@{0}".format(cache.get_ms_host())
NAS_HEALTHCHECK_COMMAND = "/opt/ericsson/enminst/bin/enm_healthcheck.sh --action nas_healthcheck --verbose"
NAS_SUCCESS_MESSAGE = "NAS HEALTHCHECK: PASSED"
LITP_CMD = 'import litp.core.base_plugin_api; password = litp.core.base_plugin_api._SecurityApi(); print password.get_password("key-for-sfs", "support")'


def check_status_of_nas(host, nas_password):
    """
    This function checks the status of nas by running the command to get status and retun OFFLINE or ONLINE based on
    output.

    :param host: nas host
    :type host: str
    :param nas_password: nas console password
    :type nas_password: str
    :return: status
    :rtype: str
    :raises EnvironError: If nas fail to 'login'
    """
    status = "OFFLINE"
    retry = 3
    with pexpect.spawn(CMD_LMS, timeout=10) as child:
        result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            log.logger.debug(login_msg[0])
            child.sendline(nas_login)
            result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
            if result == 1:
                child.sendline(nas_password)
                result = child.expect(["atnas", pexpect.EOF, pexpect.TIMEOUT])
                if not result:
                    log.logger.debug(login_msg[1])
                    child.sendline(CMD_SUMMARY + "|grep OFFLINE")
                    child.sendline("pwd")
                    result = child.expect(["home", pexpect.EOF, pexpect.TIMEOUT])
                    log.logger.debug(result)
                    log.logger.debug("The child before is : \n{0}".format(child.before))
                    log.logger.debug("The status of nas service : \n{0}".format(child.before))
                    if get_service_status(child.before, host) == "ONLINE":
                        status = "ONLINE"
                        log.logger.debug("The host - {0} status is {1}".format(host, status))
                    else:
                        status = retry_status_check(retry, host, nas_password)
                else:
                    raise EnvironError("Problem encountered trying to check the status of Nas")
            else:
                raise EnvironError("Unable to login to Nas")
        else:
            raise EnvironError("Unable to login to LMS")

    return status


def retry_status_check(retry, host, nas_password):
    """
    It checks the status of services for maximum 3 times as it takes time to get services online
    :param retry: retries services for 3 times
    :type retry: int
    :param host: nas host
    :type host: str
    :param nas_password: nas console password
    :type nas_password: str
    :return: status
    :rtype: str
    """
    status = "OFFLINE"
    while retry != 0:
        if status == "OFFLINE":
            time.sleep(120)
            status = check_status_of_nas(host, nas_password)
            retry = retry - 1
            log.logger.debug("Retrying to check the status of nas service")
        else:
            break

    return status


def get_service_status(result, host):
    """
    This function is used to determine the status of nas_instance.
    :param result: command output
    :type result: str
    :param host: command output
    :type host: str
    :return: status of nas_instance
    :rtype: list
    """
    status = "OFFLINE"
    for line in result.split('\n'):
        if "OFFLINE" in line and (host in line) and line.split(" ")[2] not in ['ManagementConsole',
                                                                               'NFSShareOfflineGrp',
                                                                               'NLMGroup', 'NicMonitorGrp',
                                                                               'TCPConnTrack', 'VIPgroup2']:
            status = "OFFLINE"
            break
        elif "OFFLINE" in line and "FAULTED" in line and host in line:
            status = "OFFLINE"
            log.logger.debug("The service {0} is in FAULTED and needs to be checked by Team Seekers".format(
                line.split(" ")[2]))
        elif "OFFLINE" in line and "FAULTED" in line:
            log.logger.debug("The service {0} is in FAULTED and needs to be checked by Team Seekers".format(
                line.split(" ")[2]))
        else:
            status = "ONLINE"
    return status


def execute_nas_command(child, command, change_required):
    """
    This function executes the nas commands - start/stop/shutdown/configure

    :param child: child object to use
    :type child: class
    :param command: command to be executed
    :type command: str
    :param change_required: The change required in nas instance
    :type change_required: str
    """
    if change_required == "configure":
        child.sendline("cd /media/config")
        child.sendline(command)
        result = child.expect(['Enter <yes|no|quit> as appropriate.',
                               pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            child.sendline("yes")
        else:
            log.logger.debug("configuration continuing...............")
        result = child.expect(['enter "no" to skip RPM install but continue with configuration updates.',
                               pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            child.sendline("no")
            result1 = child.expect(['NAS Post-install tasks completed for host', pexpect.EOF, pexpect.TIMEOUT])
            log.logger.debug("The command response code will be {0}".format(result1))
            result = child.expect(['NAS Post-install tasks completed for host', pexpect.EOF, pexpect.TIMEOUT])
            log.logger.debug("The command response code is {0}".format(result))
        else:
            log.logger.debug("configuration continuing...............")
    else:
        child.sendline(command)
        result = child.expect(["Success.", pexpect.EOF, pexpect.TIMEOUT])
        log.logger.debug("The command response code is {0}".format(result))


class NasOutage02Flow(GenericFlow):

    def execute_flow(self):
        """
        Main flow for Nas Outage 02 profile
        """
        self.state = 'RUNNING'

        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            try:
                if is_nas_accessible() and self.nas_health_check():
                    nas_slave, nas_head, nas_password = self.get_nas_instances()
                    log.logger.debug("The nas slave is {0} and nas head is {1}".format(nas_slave, nas_head))
                    self.nas_instance_change("stop", CMD_LOCK.format("stop", nas_slave), nas_head, nas_password)
                    self.teardown_list.append(partial(picklable_boundmethod(self.nas_instance_change),
                                                      "start", CMD_LOCK.format("start", nas_slave), nas_head, nas_password))
                    log.logger.debug("Sleeping for {0}, before starting nas back".format(self.SLEEP_TIME))
                    time.sleep(self.SLEEP_TIME)  # Sleep for specified hours
                    self.nas_instance_change("shutdown", CMD_RESTART, nas_slave, nas_password)
                    log.logger.debug("Sleeping for {0} sec before starting nas instance.".format(660))
                    time.sleep(660)
                    self.nas_instance_change("start", CMD_LOCK.format("start", nas_slave), nas_head, nas_password)
                    if check_status_of_nas(nas_slave, nas_password) == "ONLINE":
                        log.logger.debug("Successfully started nas. As the nas head is online we will run the "
                                         "configure script.")
                        self.nas_instance_change("configure", CMD_CONFIG, nas_head, nas_password)
                    else:
                        raise EnvironError("Could not get proper response from executing the cmd to know if "
                                           "it is successfully start")
                    if self.nas_health_check():
                        log.logger.debug("The NAS Health Check passed post execution of the NAS Usecase.")
                    else:
                        raise EnvironError("The NAS Health Check failed due to some errors in NAS instances. "
                                           "For further details on errors log into NAS server.")
                else:
                    raise EnvironError("Could not find nas/nas not reachable or The NAS Health check is failing.")

            except Exception as e:
                self.add_error_as_exception(e)

    def nas_health_check(self):
        """
        If the last 5 lines of output contains the NAS_SUCCESS_MESSAGE,
        then the ENM health check didn't encounter problems on the system
        :return: health_check_successful
        :rtype: bool
        :raises EnvironError: If nas health check fails
        """
        if check_for_active_litp_plan():
            log.logger.debug("Unable to execute ENM Health Check, active litp plan detected.")
            return
        response = run_cmd_on_ms(Command("{enminst_cmd}".format(
            enminst_cmd=NAS_HEALTHCHECK_COMMAND), timeout=600), get_pty=True)
        log.logger.debug("The return code of the coomand is {0}".format(response.rc))
        if response.rc != 0:
            raise EnvironError("The NAS Health Check Failed to complete execution.")
        response_lines = response.stdout.split("\n")
        health_check_successful = False
        for line in response_lines[-5:]:
            if NAS_SUCCESS_MESSAGE in line:
                health_check_successful = True
                break
        log.logger.debug("The NAS Health Check Passed is {0}".format(health_check_successful))
        return health_check_successful

    def nas_instance_change(self, change_required, command, host, nas_password):
        """
        This method is to execute the command to stop or start nas_instances based on the variable
        and also checks if task got properly done
        :param change_required: stop or start the nas_instance
        :type change_required: str
        :param command: command to be executed on nas
        :type command: str
        :param host: nas host to log-in
        :type host: str
        :param nas_password: nas console password for log-in
        :type nas_password: str
        :raises TimeOutError: raises if there is timeout for more than defined 30 mins
        :raises EnvironError: If nas fail to 'login'
        """
        log.logger.debug("Attempting to execute the {0} command to {1} Nas Head".format(command, change_required))
        with pexpect.spawn(CMD_LMS, timeout=200) as child:
            result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
            if not result:
                log.logger.debug(login_msg[0])
                cmd = "ssh  -o StrictHostKeyChecking=no support@{0}".format(host)
                child.sendline(nas_login)
                result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
                if result == 1:
                    child.sendline(nas_password)
                    child.sendline(cmd)
                    result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
                    if result == 1:
                        child.sendline(nas_password)
                        result = child.expect(["atnas", pexpect.EOF, pexpect.TIMEOUT])
                        if not result:
                            log.logger.debug(login_msg[1])
                            execute_nas_command(child, command, change_required)
                        else:
                            raise EnvironError(error_msg)
                    else:
                        raise EnvironError(error_msg)

                else:
                    raise EnvironError(error_msg)
            else:
                raise EnvironError("Problem encountered trying to login to LMS")

        log.logger.debug("Sleeping for 30 secs before executing next command")
        time.sleep(30)

    def get_nas_instances(self):
        """
        This function is used to filter nas_instances from command output.
        :return: nas_slave, nas_head, nas_password
        :rtype: str
        :raises TimeOutError: raises if there is timeout for more than defined 30 mins
        :raises EnvironError: If nas fail to 'login'
        """
        try:
            nas_instances = []
            nas_head, nas_slave = None, None
            log.logger.debug("Attempting to execute the {0} command to get Nas instances.".format(CMD_SHOW))

            with pexpect.spawn(CMD_LMS, timeout=50) as child:
                result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
                if not result:
                    log.logger.debug(login_msg[0])
                    child.sendline(nas_login)
                    result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
                    if result == 1:
                        nas_password = self.fetch_password_from_litp()
                        child.sendline(nas_password)
                        result = child.expect(["atnas", pexpect.EOF, pexpect.TIMEOUT])
                        if not result:
                            time.sleep(10)
                            nas_head, nas_instances = self.nas_instance(child, CMD_SHOW)
                        else:
                            raise EnvironError(error_msg)
                    else:
                        raise EnvironError(error_msg)
                else:
                    raise EnvironError("Problem encountered trying to login to LMS")

            log.logger.debug("Sleeping for 30 secs before we stop nas instance")
            time.sleep(30)
            for nas in nas_instances:
                if nas_head != nas:
                    nas_slave = nas

            return nas_slave, nas_head, nas_password
        except Exception as e:
            self.add_error_as_exception(e)

    def nas_instance(self, child, command):
        """
        This function will get the nas head and nas slave
        :param child: child object
        :type child: class
        :param command: command to be executed on nas
        :type command: str
        :return: nas_head, nas_instances
        :rtype: str, list
        :raises TimeOutError: raises if there is timeout for more than defined 30 mins
        :raises EnvironError: If nas fail to 'login'
        """
        try:
            child.sendline("pwd")
            result = child.expect(["home", pexpect.EOF, pexpect.TIMEOUT])
            nas_list = list(set(re.findall("[a-z]*atnas[0-9]*-[0-9]{2}", child.before)))
            if "h" in nas_list[0]:
                nas_head = nas_list[1]
            else:
                nas_head = nas_list[0]
            log.logger.debug("The NAS head was {0}".format(nas_head))
            if not result:
                log.logger.debug(login_msg[1])
                child.sendline(command)
                log.logger.debug(result)
                child.sendline("pwd")
                result = child.expect(["home", pexpect.EOF, pexpect.TIMEOUT])
                log.logger.debug(result)
                nas_instances = list(set(re.findall("[a-z]*atnas[0-9]*-[0-9]{2}", child.before)))
                log.logger.debug("The NAS instances were : {0}".format(nas_instances))
            else:
                raise EnvironError(error_msg)
            return nas_head, nas_instances
        except Exception as e:
            self.add_error_as_exception(e)

    @staticmethod
    def fetch_password_from_litp():
        """
        Fetch password for nas console using LITP model

        :return: nas console password
        :rtype: str
        :raises EnvironError: If fail to get password
        """
        log.logger.debug("Fetching password from LITP model")
        command = "python -c '{0}'".format(LITP_CMD)
        response = run_cmd_on_ms(command)
        if not response.ok or "ConfigParser.NoSectionError" in response.stdout:
            raise EnvironError("Issue occurred while fetching nas console password from LITP model")
        nas_password = response.stdout.strip()

        return nas_password
