from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import EnmCli05Flow


class ENMCLI_05(EnmCli05Flow):
    """
    Use Case ID:    ENMCLI_05
    Slogan:         ENMCLI collection view
    """

    NAME = "ENMCLI_05"

    def run(self):
        self.execute_flow()


enmcli_05 = ENMCLI_05()
