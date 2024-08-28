from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui07Flow


class SECUI_07(Secui07Flow):
    """
    Use Case ID:    SECUI_07
    Slogan:         Create Target Group
    """
    NAME = "SECUI_07"

    def run(self):
        self.execute_flow()


secui_07 = SECUI_07()
