from enmutils_int.lib.profile_flows.netex_flows.netex_flow import Netex07Flow


class NETEX_07(Netex07Flow):
    """
    Use Case id:            NETEX_07
    Slogan:                 Export Collections of Collections
    """

    NAME = "NETEX_07"

    def run(self):
        self.execute_flow()


netex_07 = NETEX_07()
