from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow
from enmutils_int.lib.nhm_rest_nbi import NHM_REST_NBI_KPI_OPERATION


class NhmNbi06Flow(NhmRestNbiFlow):

    def execute_flow(self):
        """
        Executes the Main flow for Nhm_rest_nbi_06 profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        while self.keep_running():
            try:
                self.sleep_until_day()
                fdn_values = self.fdn_format(allocated_nodes)
                pre_defined_kpis = self.nhm_rest_pre_defined_kpi(self.get_list_all_kpis(user))
                self.kpi_execution_nhm_rest_pre_defined(user, fdn_values, pre_defined_kpis, NHM_REST_NBI_KPI_OPERATION)

            except Exception as e:
                self.add_error_as_exception(e)
