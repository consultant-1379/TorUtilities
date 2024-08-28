from enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow import Nhm0102


class NHM_SETUP(Nhm0102):
    """
    Use Case ID:            NHM_SETUP
    Slogan:                 Create and Activate Node Counter KPIs
    """
    NAME = "NHM_SETUP"

    def run(self):
        self.execute_flow()


nhm_setup = NHM_SETUP()
