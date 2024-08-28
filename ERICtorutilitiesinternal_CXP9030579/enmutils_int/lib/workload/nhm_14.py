from enmutils_int.lib.profile_flows.nhm_flows.nhm_14_flow import Nhm14Flow


class NHM_14(Nhm14Flow):
    """
    Use Case ID:            NHM 14
    Slogan:                 Criteria based KPIs
    """
    NAME = "NHM_14"

    def run(self):
        self.execute_flow()


nhm_14 = NHM_14()
