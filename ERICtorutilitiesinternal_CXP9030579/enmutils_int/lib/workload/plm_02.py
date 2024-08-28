from enmutils_int.lib.profile_flows.plm_flows.plm_02_flow import Plm02Flow


class PLM_02(Plm02Flow):
    """
    Use Case ID:        PLM_02
    Slogan:             Physical Link Management
    """

    NAME = "PLM_02"

    def run(self):
        self.execute_flow()


plm_02 = PLM_02()
