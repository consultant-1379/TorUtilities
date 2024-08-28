from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui08Flow


class SECUI_08(Secui08Flow):
    """
    Use Case ID:    SECUI_08
    Slogan:         Edit Target Group
    """
    NAME = "SECUI_08"

    def run(self):

        self.execute_flow()


secui_08 = SECUI_08()
