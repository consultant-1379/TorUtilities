from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui05Flow


class SECUI_05(Secui05Flow):
    """
    Use Case ID:    SECUI_05
    Slogan:         Create 750 Roles (Custom, COM, COM Alias)
    """
    NAME = "SECUI_05"

    def run(self):
        self.execute_flow()


secui_05 = SECUI_05()
