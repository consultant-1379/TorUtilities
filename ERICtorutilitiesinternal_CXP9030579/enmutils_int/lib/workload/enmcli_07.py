from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow0708 import ENMCLI0708Flow


class ENMCLI_07(ENMCLI0708Flow):
    """
    Use Case ID:    ENMCLI_07
    Slogan:         CMCLI Create and Delete
    """

    NAME = "ENMCLI_07"

    def run(self):
        self.execute_flow()


enmcli_07 = ENMCLI_07()
