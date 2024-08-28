import signal
import time

from requests.exceptions import HTTPError

from enmutils.lib import cache, log, process, shell
from enmutils.lib.enm_user_2 import EnmRole, Target
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib import enm_deployment
from enmutils_int.lib.enm_user import (CustomUser, get_workload_admin_user,
                                       user_exists)
from enmutils_int.lib.services import deployment_info_helper_methods
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm


class FmBnsiNbi(object):

    def __init__(self):
        self.username = "bnsiman01"   # username has to be bnsiman01 for bnsi nbi
        self.password = "TestPassw0rd"
        self.roles = ['FM_BNSINBI_Administrator', 'FM_BNSINBI_Operator']
        self.pib_parameter = "bnsiNbiEnabled"
        self.fm_vip = ""
        self.bnsi_service = ""
        self.bnsi_enabled = False

    def create_bnsiman_user_and_enable_bnsi_nbi(self):
        """
        Checks if bnsiman01 is present in ENM, if not will create and enables BNSI NBI via a PIB parameter
        """
        cloud_native = cache.is_enm_on_cloud_native()
        self.bnsi_service = "nbi-bnsi-fm" if cloud_native else "bnsiserv"
        self.fm_vip = (deployment_info_helper_methods.get_cloud_native_service_vip("nbi-bnsi-fm") if cloud_native
                       else enm_deployment.get_values_from_global_properties("svc_FM_vip_ipaddress")[0])
        log.logger.debug("BNSI service name : {0}, FM VIP address : {1}".format(self.bnsi_service, self.fm_vip))
        bnsiman_user_exists = self.check_and_create_bnsiman_user()
        if bnsiman_user_exists:
            response = update_pib_parameter_on_enm(self.bnsi_service, self.pib_parameter, "true")
            if response:
                self.bnsi_enabled = True
                log.logger.debug("Successfully enabled BNSI-NBI : {0}".format(self.bnsi_enabled))
        else:
            log.logger.debug("bnsiman user creation failed,check profile log for more details")

    def create_bnsiman_user(self):
        """
        creates a custom user bnsiman for BNSI operations
        :return: True if user exists else False
        :rtype: bool
        :raises EnmApplicationError: is user session is not established
        """
        retries = 0
        sleep_time = 180
        roles = list(EnmRole(role) if isinstance(role, basestring) else role for role in self.roles)
        targets = [Target("ALL")]
        bnsiman_user = CustomUser(username=self.username, password=self.password, roles=roles, targets=targets,
                                  fail_fast=False, safe_request=False, retry=True, persist=False, keep_password=True)
        while retries < 3:
            try:
                bnsiman_user.create()
                log.logger.debug("bnsiman user created successfully in ENM, sleeping for {0} sec before trying "
                                 "to login".format(sleep_time))
                time.sleep(sleep_time)
                break
            except Exception as e:
                log.logger.debug("Exception : {0}".format(e))
                log.logger.debug("Failed to create bnsiman user in ENM, sleeping for {0} "
                                 "seconds before retrying.".format(sleep_time))
                time.sleep(sleep_time)
                retries += 1
        session_established = bnsiman_user.is_session_established()
        if not session_established:
            raise EnmApplicationError("bnsiman user is unable to login to ENM, "
                                      "please check the profile log for more details")
        else:
            return True

    def check_and_create_bnsiman_user(self):
        """
        Checks in ENM if bnsiman user exists, if not creates one
        :return: True if user exists else False
        :rtype: bool
        """
        try:
            user_available = user_exists(get_workload_admin_user(), search_for_username=self.username)
            log.logger.debug("{0} user already exists in ENM".format(self.username))
            return user_available
        except HTTPError as e:
            if e.response.status_code == 404 and 'Not Found' in e.response.reason:
                log.logger.debug("Response : {0}".format(e.response.reason))
                log.logger.debug("{0} user is not found in ENM, creating the user now".format(self.username))
                user_available = self.create_bnsiman_user()
                return user_available
            else:
                log.logger.debug("Exception encountered while checking if bnsiman user exists : {0}".format(e))

    @staticmethod
    def check_and_remove_if_bnsi_sendalarms_is_already_running():
        """
        Checks for any BNSI NBI SSH process running on the wlvm and will clear that process
        """
        pid_list = []
        cmd = "pgrep -f 'SendAlarms bnsitest'"
        log.logger.debug("Checking if the SSH connection for BNSI SendAlarms is already running")
        try:
            response = shell.run_local_cmd(cmd)
            if response.ok and response.stdout.strip():
                pid_list = response.stdout.strip().split("\n")
                log.logger.debug("Found these PID(s) for BNSI NBI: {0}".format(pid_list))
            for pid in pid_list:
                process.kill_process_id(int(pid), signal.SIGINT)
                log.logger.debug("cleared the process with PID: {0}".format(pid))
        except Exception as e:
            raise EnvironError("Encountered exception while trying to fetch and terminate SSH session, "
                               "Exception : {0}".format(e))

    def check_if_bnsi_session_is_available_and_close_it(self, child=None):
        """
        Will check and remove if any existing BNSI NBI session is open and will open a new bnsi nbi ssh session
        """
        try:
            if child and child.isalive():
                log.logger.debug("Found a live terminal, closing it")
                child.sendcontrol('c')
                child.close()
                log.logger.debug("terminated the old SSH session terminal")
            time.sleep(10)
            self.check_and_remove_if_bnsi_sendalarms_is_already_running()
            log.logger.debug("Sleeping for 120 secs before opening a new SSH connection")
            time.sleep(120)
        except Exception as e:
            log.logger.debug("Exception encountered while opening SSH session towards FM VIP, "
                             "Exception : {0}".format(str(e)))

    def _teardown(self):
        """
        Disables BNSI NBI during the teardown
        """
        log.logger.debug("Disabling BNSI NBI")
        self.check_and_remove_if_bnsi_sendalarms_is_already_running()
        response = enm_deployment.update_pib_parameter_on_enm(self.bnsi_service, self.pib_parameter, "false")
        if response:
            log.logger.debug('Disabled BNSI NBI during teardown')
