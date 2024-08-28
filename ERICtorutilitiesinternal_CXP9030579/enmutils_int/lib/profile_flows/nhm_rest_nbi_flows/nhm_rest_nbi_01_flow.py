from enmutils.lib import log
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow
from enmutils_int.lib.nhm_rest_nbi import LAST_ROP_REQUEST


class NhmNbi01Flow(NhmRestNbiFlow):

    def execute_flow(self):
        """
        Executes the Main flow for Nhm_rest_nbi_01 profile
        """
        self.state = "RUNNING"
        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()
        log.logger.debug("operator_users{0}, nodes_verified_on_enm{1}".format(operator_users, nodes_verified_on_enm))
        while self.keep_running():

            try:
                fdn_values = self.fdn_format(nodes_verified_on_enm)
                node_level_kpi = self.nhm_rest_nbi_node_level_kpi(self.get_list_all_kpis(operator_users[0]))
                self.kpi_execution_nhm_rest_nbi(operator_users[0], node_level_kpi, fdn_values, LAST_ROP_REQUEST)

            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()
