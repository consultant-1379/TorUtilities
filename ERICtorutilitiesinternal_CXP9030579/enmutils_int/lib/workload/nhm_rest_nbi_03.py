from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_03_flow import NhmNbi03Flow


class NHM_REST_NBI_03(NhmNbi03Flow):

    """
    Use Case ID:            NHM_REST_NBI_03
    Slogan:                 Restful access to KPI service to read KPI values of 10 KPIs created by NHM_SETUP
    """
    NAME = "NHM_REST_NBI_03"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_03 = NHM_REST_NBI_03()
