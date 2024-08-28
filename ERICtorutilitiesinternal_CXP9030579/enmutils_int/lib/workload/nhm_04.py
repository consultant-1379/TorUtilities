from enmutils_int.lib.profile_flows.nhm_flows.nhm_04_flow import Nhm04


class NHM_04(Nhm04):
    """
    Use Case ID:            NHM_04
    Slogan:                 Execute Network Health Monitor user interface with 2 concurrent users
    """
    NAME = "NHM_04"

    def run(self):
        self.execute_flow()


nhm_04 = NHM_04()
