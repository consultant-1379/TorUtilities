from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_07_flow import NhmRestNbi07Flow


class NHM_REST_NBI_07(NhmRestNbi07Flow):

    """
    Use Case ID:            NHM_REST_NBI_07
    Slogan:                 Restful access to KPI service to execute the list All KPIs
    """
    NAME = "NHM_REST_NBI_07"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_07 = NHM_REST_NBI_07()
