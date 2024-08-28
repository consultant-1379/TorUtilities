from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_setup_flow import NhmRestNbiSetup


class NHM_REST_NBI_SETUP(NhmRestNbiSetup):
    """
    Use Case ID:            NHM_REST_NBI_SETUP
    Slogan:                 Create and Activate Node level KPIs
    """
    NAME = "NHM_REST_NBI_SETUP"

    def run(self):
        self.execute_flow()


nhm_rest_nbi_setup = NHM_REST_NBI_SETUP()
