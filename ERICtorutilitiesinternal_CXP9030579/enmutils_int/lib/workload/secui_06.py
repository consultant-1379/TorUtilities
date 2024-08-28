from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui06Flow


class SECUI_06(Secui06Flow):
    """
    Use Case ID:    SECUI_06
    Slogan:         Get Standalone Credentials
    """
    NAME = "SECUI_06"

    def run(self):
        self.execute_flow()


secui_06 = SECUI_06()
