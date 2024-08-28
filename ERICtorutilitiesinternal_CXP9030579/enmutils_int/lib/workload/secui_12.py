from enmutils_int.lib.profile_flows.secui_flows.secui_flow import Secui12Flow


class SECUI_12(Secui12Flow):
    """
    Use Case ID:    SECUI_12
    Slogan:         SSO Authentication: External LDAP User with Federated Identity Management Service (FIDM).
    """
    NAME = "SECUI_12"

    def run(self):
        self.execute_flow()


secui_12 = SECUI_12()
