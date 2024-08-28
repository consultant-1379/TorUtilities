from enmutils_int.lib.profile_flows.nhm_flows.nhm_11_flow import Nhm11


class NHM_11(Nhm11):
    """
    Use Case ID:            NHM_11
    Slogan:                 Execute Network Health Monitor user interface with 1 concurrent user
    """

    NAME = "NHM_11"

    def run(self):
        self.execute_flow()


nhm_11 = NHM_11()
