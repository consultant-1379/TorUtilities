from enmutils_int.lib.profile_flows.plm_flows.plm_01_flow import Plm01Flow


class PLM_01(Plm01Flow):
    """
    Use Case ID:        PLM_01
    Slogan:             Physical Link Management
    """

    NAME = "PLM_01"

    def run(self):
        self.execute_flow()


plm_01 = PLM_01()
