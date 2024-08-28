from enmutils_int.lib.profile_flows.nhm_flows.nhm_03_flow import Nhm03


class NHM_03(Nhm03):

    """
    Use Case ID:            NHM_03
    Slogan:                 Simultaneous KPI Users
    """
    NAME = "NHM_03"

    def run(self):
        self.execute_flow()


nhm_03 = NHM_03()
