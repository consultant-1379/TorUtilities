from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import EnmCli03Flow


class ENMCLI_03(EnmCli03Flow):
    """
    Use case ID:        ENMCLI_03
    Slogan:             ENMCLI scripting sessions
    """

    NAME = "ENMCLI_03"

    def run(self):
        self.execute_flow()


enmcli_03 = ENMCLI_03()
