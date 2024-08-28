from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_02_flow import NhmNbi02Flow


class NHM_REST_NBI_02(NhmNbi02Flow):

    """
    Use Case ID:            NHM_REST_NBI_02
    Slogan:                 Restful access to KPI service to read KPI values of 5KPIs created by NHM_NBI_SETUP
    """
    NAME = "NHM_REST_NBI_02"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_02 = NHM_REST_NBI_02()
