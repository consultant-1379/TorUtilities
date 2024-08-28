from enmutils_int.lib.profile_flows.netex_flows.netex_flow import Netex05Flow


class NETEX_05(Netex05Flow):
    """
    Use case id:            NETEX_05
    Slogan:                 Create Custom-Topologies
    """

    NAME = "NETEX_05"

    def run(self):
        self.execute_flow()


netex_05 = NETEX_05()
