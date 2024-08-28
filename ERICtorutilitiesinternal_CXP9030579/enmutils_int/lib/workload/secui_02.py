from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui02Flow


class SECUI_02(Secui02Flow):
    """
    Use Case ID:        SECUI_02
    Slogan:             Create & Delete user roles
    """
    NAME = "SECUI_02"

    def run(self):
        self.execute_flow()


secui_02 = SECUI_02()
