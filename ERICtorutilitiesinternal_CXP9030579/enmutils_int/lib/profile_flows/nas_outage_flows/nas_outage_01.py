import time
from functools import partial
import pexpect
from enmutils.lib import log, cache
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_flow import is_nas_accessible


def check_status_of_nas():
    """
    This function checks the status of nas by running the command to get status and retuns OFFLINE or ONLINE based on output
    :return: status
    :rtype: str
    :raises EnvironError: If nas or lms fail to 'login'
    """
    status = "OFFLINE"
    cmd = "ssh root@{0}".format(cache.get_ms_host())
    password_format = "[pP]assword:"
    with pexpect.spawn(cmd, timeout=10) as child:
        lms_login_status = "root@ieatlms"
        result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
        if not result:
            log.logger.debug("logged into LMS")
            cmd = "ssh  -o StrictHostKeyChecking=no support@nasconsole"
            child.sendline(cmd)
            result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
            if result == 1:
                child.sendline("symantec")
                result = child.expect(["atnas", pexpect.EOF, pexpect.TIMEOUT])
                if not result:
                    log.logger.debug("logged in to nas")
                    child.sendline("/opt/VRTSnas/clish/bin/clish -u master -c 'nfs server status'")
                    result = child.expect(["ONLINE", pexpect.EOF, pexpect.TIMEOUT])
                    if not result:
                        status = "ONLINE"
                        log.logger.debug("Nas online")
                    else:
                        log.logger.debug("Nas offline")
                else:
                    raise EnvironError("Problem encountered trying to check the status of Nas")
            else:
                raise EnvironError("Unable to login to Nas")
        else:
            raise EnvironError("Unable to login to LMS")
    return status


class NasOutage01Flow(GenericFlow):
    EXPIRE_TIME = 30

    def execute_flow(self):
        """
        Main flow for Nas Outage 01 profile
        """
        self.state = 'RUNNING'

        try:
            if is_nas_accessible():
                self.nfs_server_change("stop")
                self.teardown_list.append(partial(picklable_boundmethod(self.nfs_server_change),
                                                  "start"))
                self.state = "SLEEPING"
                log.logger.debug("Sleeping for {0}, before starting nas back".format(self.SLEEP_TIME))
                time.sleep(self.SLEEP_TIME)  # Sleep for specified hours
                self.state = "RUNNING"
                self.nfs_server_change("start")
            else:
                raise EnvironError("Could not find nas/nas not reachable")

        except Exception as e:
            self.add_error_as_exception(e)

    def nfs_server_change(self, change_required):
        """
        This method is to execute the command to stop or start nas based on the variable
        and also checks if task got properly done
        :param change_required: stop or start the nas
        :type change_required: str
        :raises TimeOutError: raises if there is timeout for more than defined 30 mins
        :raises EnvironError: raises if there is login issue with NAS or LMS
        """
        try:
            cmd_lock = "sudo /opt/VRTSnas/clish/bin/clish -u master -c 'nfs server {0}'".format(change_required)
            log.logger.debug("Attempting to execute the {0} command to stop Nas".format(cmd_lock))

            cmd = "ssh root@{0}".format(cache.get_ms_host())
            password_format = "[pP]assword:"
            with pexpect.spawn(cmd, timeout=50) as child:
                lms_login_status = "root@ieatlms"
                result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
                if not result:
                    log.logger.debug("logged into LMS")
                    cmd = "ssh  -o StrictHostKeyChecking=no support@nasconsole"
                    child.sendline(cmd)
                    result = child.expect([lms_login_status, password_format, pexpect.EOF, pexpect.TIMEOUT])
                    if result == 1:
                        child.sendline("symantec")
                        result = child.expect(["atnas", pexpect.EOF, pexpect.TIMEOUT])
                        if not result:
                            log.logger.debug("logged in to nas")
                            child.sendline(cmd_lock)
                            result = child.expect(["Success.", pexpect.EOF, pexpect.TIMEOUT])
                            log.logger.debug(result)
                        else:
                            raise EnvironError("Problem encountered trying to nas login")
                    else:
                        raise EnvironError("Problem encountered trying to nas login")
                else:
                    raise EnvironError("Problem encountered trying to login to LMS")

            log.logger.debug("Sleeping for 30 secs before executing next command")
            time.sleep(30)
            if check_status_of_nas() == "ONLINE" if change_required == "start" else "OFFLINE":
                log.logger.debug("Successfully {0} nas".format(change_required))
            else:
                raise EnvironError("Could not get proper response from executing the cmd to know if "
                                   "it is successfully {0}".format(change_required))

        except Exception as e:
            self.add_error_as_exception(e)
