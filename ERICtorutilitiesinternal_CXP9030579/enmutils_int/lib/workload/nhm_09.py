from enmutils_int.lib.profile_flows.nhm_flows.nhm_09_flow import Nhm09


class NHM_09(Nhm09):
    """
    Use Case ID:            NHM_09
    Slogan:                 Execute Network Health Monitor user interface with 5 concurrent users
    """
    NAME = "NHM_09"

    def run(self):
        self.execute_flow()


nhm_09 = NHM_09()
