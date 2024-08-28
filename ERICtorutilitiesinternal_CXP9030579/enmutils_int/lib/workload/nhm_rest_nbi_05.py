from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_05_flow import NhmNbi05Flow


class NHM_REST_NBI_05(NhmNbi05Flow):

    """
    Use Case ID:            NHM_REST_NBI_05
    Slogan:                 perform CRUD operations on KPIs from external NBI
    """
    NAME = "NHM_REST_NBI_05"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_05 = NHM_REST_NBI_05()
