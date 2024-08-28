from enmutils_int.lib.profile_flows.nhm_flows.nhm_05_flow import Nhm05


class NHM_05(Nhm05):
    """
       Use Case ID:    NHM_05
       Slogan:         Simultaneous Multi-Node NHM Users
       """
    NAME = "NHM_05"

    def run(self):
        self.execute_flow()


nhm_05 = NHM_05()
