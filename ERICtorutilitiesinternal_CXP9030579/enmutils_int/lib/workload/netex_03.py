from enmutils_int.lib.profile_flows.netex_flows.netex_flow import Netex03Flow


class NETEX_03(Netex03Flow):
    """
    Use Case id:            NETEX_03
    Slogan:                 Find All Locked Cells
    """

    NAME = "NETEX_03"

    def run(self):
        self.execute_flow()


netex_03 = NETEX_03()
