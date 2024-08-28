from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_06_flow import EnmCli06Flow


class ENMCLI_06(EnmCli06Flow):
    """
    Use Case ID:    ENMCLI_06
    Slogan:         CMCLI Update
    """

    NAME = "ENMCLI_06"

    def run(self):
        self.execute_flow()


enmcli_06 = ENMCLI_06()
