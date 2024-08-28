from enmutils_int.lib.profile_flows.nhm_flows.nhm_07_flow import Nhm07


class NHM_07(Nhm07):
    """
    Use Case ID:            NHM_07
    Slogan:                 Simultaneous Multi-Node NHM Users (Cell KPI)
    """

    NAME = "NHM_07"

    def run(self):
        self.execute_flow()


nhm_07 = NHM_07()
