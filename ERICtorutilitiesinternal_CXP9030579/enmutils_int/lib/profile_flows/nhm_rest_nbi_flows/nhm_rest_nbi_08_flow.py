import random
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow
from enmutils_int.lib.nhm_rest_nbi import NHM_REST_NBI_KPI_METRICS, NhmRestNbiKpi


class NhmRestNbi08Flow(NhmRestNbiFlow):
    """
    Class to run the flow for Nhm_rest_nbi_08 profile
    """

    def execute_flow(self):
        """
        Executes the flow of NHM_08 profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        while self.keep_running():
            self.sleep_until_time()
            try:
                all_kpis = [value['id'] for value in self.get_list_all_kpis(users[0])]
                random_kpi = random.sample(all_kpis, 5)
                if random_kpi:
                    NhmRestNbiKpi().activation_status(users[0], random_kpi)
                    self.calculation_metrics(users[0])
                else:
                    raise EnmApplicationError("No kpi's available for this iteration")
            except Exception as e:
                self.add_error_as_exception(e)

    def calculation_metrics(self, user):
        """
        This method is to execute the Rest request as part nhm nbi 08profile flow.
        :param user: username to send the rest call.
        :type user: list
        :raises EnmApplicationError: if there is error in response from ENM
        """
        try:
            response = user.get(NHM_REST_NBI_KPI_METRICS, headers=JSON_SECURITY_REQUEST)
            if response.status_code != 200:
                raise EnmApplicationError("Unexpected response received {0}".format(response.json()))
            log.logger.debug("Response : {0}".format(response.json()))
        except Exception as e:
            self.add_error_as_exception(e)
