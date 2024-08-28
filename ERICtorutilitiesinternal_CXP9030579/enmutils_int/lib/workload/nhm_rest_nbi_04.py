from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_04_flow import NhmNbi04Flow


class NHM_REST_NBI_04(NhmNbi04Flow):

    """
    Use Case ID:            NHM_REST_NBI_04
    Slogan:                 Restful access to KPI service to read KPI values of 10KPIs created by NHM_SETUP
    """
    NAME = "NHM_REST_NBI_04"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_04 = NHM_REST_NBI_04()
