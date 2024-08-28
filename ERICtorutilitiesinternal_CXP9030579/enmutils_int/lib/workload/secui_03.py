from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui03Flow


class SECUI_03(Secui03Flow):
    """
    Use Case ID:    SECUI_03
    Slogan:         Utility Profile: Password Aging
    """
    NAME = "SECUI_03"

    def run(self):
        self.execute_flow()


secui_03 = SECUI_03()
