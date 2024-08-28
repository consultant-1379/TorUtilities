# ********************************************************************
# Name    : Network Connectivity Manager-Metro Ethernet Forum
# Summary : It allows the user to perform realign a list of nodes and
#           links when the rest call is invoked.
# ********************************************************************

from enmutils_int.lib.ncm_manager import ncm_rest_query, fetch_ncm_vm
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib import log

REALIGN_ENDPOINT = "/ncm/rest/management/realign"


class NcmMef01Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        try:
            if fetch_ncm_vm() in ("1.1.1.1", None):
                raise EnvironError("NCM VM is not configured in this deployment")
            while self.keep_running():
                self.sleep_until_day()
                for user in users:
                    log.logger.debug("Executing {0} service discovery with user: {1}".format(self.NAME, user))
                    try:
                        ncm_rest_query(user, REALIGN_ENDPOINT)
                    except Exception as e:
                        log.logger.debug("{0} error response is {1}".format(self.NAME, e.message))
                        self.add_error_as_exception(EnmApplicationError("Unable to send post alignment to {0}: {1}"
                                                                        .format(self.NAME, str(e))))
        except EnvironError as e:
            self.add_error_as_exception(EnvironError(e))
