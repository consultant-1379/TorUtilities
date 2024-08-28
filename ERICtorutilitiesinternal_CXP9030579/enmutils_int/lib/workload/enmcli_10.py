from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_10_flow import ENMCLI10Flow


class ENMCLI_10(ENMCLI10Flow):
    """
    Use Case ID:    ENMCLI_10
    Slogan:         CM CLI Write For YANG Nodes
    """

    NAME = "ENMCLI_10"

    def run(self):
        self.execute_flow()


enmcli_10 = ENMCLI_10()
