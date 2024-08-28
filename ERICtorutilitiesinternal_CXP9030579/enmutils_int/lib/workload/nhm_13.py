from enmutils_int.lib.profile_flows.nhm_flows.nhm_13_flow import Nhm13Flow


class NHM_13(Nhm13Flow):
    """
    Use Case ID:            NHM 13
    Slogan:                 Real Time KPI
    """
    NAME = "NHM_13"

    def run(self):
        self.execute_flow()


nhm_13 = NHM_13()
