# ********************************************************************
# Name    : Network Connectivity Manager - Virtual Private Network
# Summary : It allows the user to perform realign a list of nodes and
#           links when the rest call is invoked.
# ********************************************************************

import json
import time

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.ncm_manager import lcm_db_restore, ncm_rest_query, fetch_ncm_vm
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class NcmL3Vpn01Flow(GenericFlow):

    VPN_LCM_ACTIVATE_ENDPOINT = "/ncm/seam/resource/rest/management/service/activate"
    VPN_LCM_DEACTIVATE_ENDPOINT = "/ncm/seam/resource/rest/management/service/deactivate"

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        try:
            if fetch_ncm_vm() in ("1.1.1.1", None):
                raise EnvironError("NCM VM is not configured in this deployment")
            while self.keep_running():
                try:
                    self.sleep_until_day()
                    if self.RUN_RESTORE:
                        lcm_db_restore(self.RESTORE_FILE_NAME)
                        log.logger.debug("Sleeping for five minutes after {0} db restore activity".format(self.NAME))
                        time.sleep(60 * 5)
                    for each_run in range(self.NUMBER_OF_RUNS):
                        self.vpn_lcm_serv_act_deact(user, self.VPN_LCM_ACTIVATE_ENDPOINT, self.SLEEP_TIME_AFTER_ACT,
                                                    each_run + 1, "Act")
                        self.vpn_lcm_serv_act_deact(user, self.VPN_LCM_DEACTIVATE_ENDPOINT, self.SLEEP_TIME_AFTER_DEACT,
                                                    each_run + 1, "Deact")
                        if each_run + 1 == self.NUMBER_OF_RUNS:
                            log.logger.debug("Successfully completed executing VPN LCM activation and deactivation for "
                                             "{0} times".format(self.NUMBER_OF_RUNS))
                except Exception as e:
                    self.add_error_as_exception(e)
        except EnvironError as e:
            self.add_error_as_exception(EnvironError(e))

    def vpn_lcm_serv_act_deact(self, user, op_type, sleep_time, run_value, serv_type):
        """
        Performs vpn lcm activation/deactivation based on rest end point and provided services
        :type user: `enm_user_2.User` object
        :param user: enm user to perform rest operation
        :param op_type: rest end point activation/deactivation
        :type op_type: str
        :param sleep_time: time to wait in seconds after service activation/deactivation
        :type sleep_time: int
        :param run_value: run/iteration number
        :type run_value: int
        :param serv_type: service type activation/deactivation
        :type serv_type: str
        :raises EnmApplicationError: when rest call failed to execute
        """
        log.logger.debug("Starting VPN LCM {0}ivation: {1}".format(serv_type, run_value))
        list_of_services = self.LIST_OF_LCM_SERVICES or [
            self.SERVICE_PREFIX + str(ser_num).zfill(2) for ser_num in range(1, self.MAX_SERVICES + 1)]
        update_json = {"serviceType": self.SERVICE_TYPE, "services": list_of_services}
        data = json.dumps(update_json)
        try:
            ncm_rest_query(user, op_type, data)
            log.logger.debug("Completed VPN LCM {0}ivation: {1}".format(serv_type, run_value))
            log.logger.debug("Sleeping for {0} seconds after VPN lcm {1}ivation run {2}".format(sleep_time, serv_type,
                                                                                                run_value))
            time.sleep(sleep_time)
        except Exception as e:
            log.logger.debug("{0} error response is {1}".format(self.NAME, e.message))
            raise EnmApplicationError("Unable to send post alignment to {0}: {1}".format(self.NAME, str(e)))
