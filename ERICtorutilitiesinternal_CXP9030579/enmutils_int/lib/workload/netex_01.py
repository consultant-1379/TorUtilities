from enmutils_int.lib.profile_flows.netex_flows.netex_flow import Netex01Flow


class NETEX_01(Netex01Flow):
    """
    Use Case id:            NETEX_01
    Slogan:                 Network Explorer Search
    """

    NAME = "NETEX_01"

    def run(self):
        self.execute_flow()


netex_01 = NETEX_01()
