from enmutils_int.lib.profile_flows.nhm_flows.nhm_06_flow import Nhm06


class NHM_06(Nhm06):
    """
    Use Case ID:            NHM_06
    Slogan:                 Simultaneous Multi-Node NHM Users (Cell KPI)
    """

    NAME = "NHM_06"

    def run(self):
        self.execute_flow()


nhm_06 = NHM_06()
