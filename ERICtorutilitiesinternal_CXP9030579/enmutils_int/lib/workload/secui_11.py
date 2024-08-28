from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui11Flow


class SECUI_11(Secui11Flow):

    """
    Use Case id:        Secui_11
    Slogan:             Target Based Access Control
    """
    NAME = "SECUI_11"

    def run(self):
        self.execute_flow()


secui_11 = SECUI_11()
