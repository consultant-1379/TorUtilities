from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import EnmCli01Flow


class ENMCLI_01(EnmCli01Flow):
    """
    Use case ID:        ENMCLI_01
    Slogan:             ENMCLI Web Browser user runs commands towards the whole network
    """

    NAME = "ENMCLI_01"

    def run(self):
        self.execute_flow()


enmcli_01 = ENMCLI_01()
