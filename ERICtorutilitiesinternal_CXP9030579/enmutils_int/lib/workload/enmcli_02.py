from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import EnmCli02Flow


class ENMCLI_02(EnmCli02Flow):
    """
    Use case ID:        ENMCLI_02
    Slogan:             ENMCLI Web Browser users
    """

    NAME = "ENMCLI_02"

    def run(self):

        self.execute_flow()


enmcli_02 = ENMCLI_02()
