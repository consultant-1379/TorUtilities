from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui10Flow


class SECUI_10(Secui10Flow):
    """
    Use Case ID:    SECUI_10
    Slogan:         COM Authentication and Authorization (AA) request
    """
    NAME = "SECUI_10"

    def run(self):
        self.execute_flow()


secui_10 = SECUI_10()
