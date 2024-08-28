from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_08_flow import NhmRestNbi08Flow


class NHM_REST_NBI_08(NhmRestNbi08Flow):

    """
    Use Case ID:            NHM_REST_NBI_08
    Slogan:                 Restful access to KPI service to check the activation status and calculation metrics
    """
    NAME = "NHM_REST_NBI_08"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_08 = NHM_REST_NBI_08()
