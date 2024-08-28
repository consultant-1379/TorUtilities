from enmutils_int.lib.profile_flows.nhm_flows.nhm_12_flow import Nhm12


class NHM_12(Nhm12):
    """
    Use Case ID:            NHM 12
    Slogan:                 FM Alarm for KPI results in breach of threshold
    """
    NAME = "NHM_12"

    def run(self):
        self.execute_flow()


nhm_12 = NHM_12()
