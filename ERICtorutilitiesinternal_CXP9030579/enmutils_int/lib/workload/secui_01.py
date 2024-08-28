from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui01Flow


class SECUI_01(Secui01Flow):
    """
    Use Case ID:        SECUI_01
    Slogan:             Create user accounts
    """
    NAME = "SECUI_01"

    def run(self):
        self.execute_flow()


secui_01 = SECUI_01()
