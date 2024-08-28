from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow
from enmutils_int.lib.nhm_rest_nbi import LAST_ROP_REQUEST


class NhmNbi03Flow(NhmRestNbiFlow):

    def execute_flow(self):
        """
        Executes the Main flow for Nhm_rest_nbi_03 profile
        """
        self.state = "RUNNING"
        operator_users, nodes_verified_on_enm = self.setup_nhm_profile()
        while self.keep_running():
            try:
                node_level_kpi = self.nhm_node_level_kpi(self.get_list_all_kpis(operator_users[0]))
                self.kpi_execution(operator_users[0], node_level_kpi, self.fdn_format(nodes_verified_on_enm),
                                   LAST_ROP_REQUEST)
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()
