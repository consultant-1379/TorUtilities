from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui09Flow


class SECUI_09(Secui09Flow):
    """
    Use Case ID:    SECUI_09
    Slogan:         Delete Target Group
    """
    NAME = "SECUI_09"

    def run(self):
        self.execute_flow()


secui_09 = SECUI_09()
