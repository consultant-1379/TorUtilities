from enmutils.lib import log
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow


class NhmRestNbi07Flow(NhmRestNbiFlow):

    def execute_flow(self):
        """
        Executes the Main flow for Nhm_rest_nbi_07 profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        while self.keep_running():
            self.sleep_until_time()
            try:
                self.get_list_all_kpis(users[0])
                log.logger.debug("Successfully fetched list of all kpis")
            except Exception as e:
                self.add_error_as_exception(e)
