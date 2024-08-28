from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_06_flow import NhmNbi06Flow


class NHM_REST_NBI_06(NhmNbi06Flow):

    """
    Use Case ID:            NHM_REST_NBI_06
    Slogan:                 Restful access to edit KPIs from external NBI
    """
    NAME = "NHM_REST_NBI_06"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_06 = NHM_REST_NBI_06()
