from enmutils_int.lib.profile_flows.nhm_flows.nhm_10_flow import Nhm10


class NHM_10(Nhm10):
    """
    Use Case ID:            NHM_10
    Slogan:                 Execute Network Health Monitor user interface with 2 concurrent users
    """

    NAME = "NHM_10"

    def run(self):
        self.execute_flow()


nhm_10 = NHM_10()
