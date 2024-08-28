from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import EnmCli08Flow


class ENMCLI_08(EnmCli08Flow):
    """
    Use Case ID:    ENMCLI_08
    Slogan:         CMCLI Create Set Delete
    """

    NAME = "ENMCLI_08"

    def run(self):
        self.execute_flow()


enmcli_08 = ENMCLI_08()
