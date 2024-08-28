from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_01_flow import NhmNbi01Flow


class NHM_REST_NBI_01(NhmNbi01Flow):

    """
    Use Case ID:            NHM_REST_NBI_01
    Slogan:                 Restful access to use KPI service
    """
    NAME = "NHM_REST_NBI_01"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_01 = NHM_REST_NBI_01()
