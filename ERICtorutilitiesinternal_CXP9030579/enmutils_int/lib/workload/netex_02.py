from enmutils_int.lib.profile_flows.netex_flows.netex_flow import Netex02Flow


class NETEX_02(Netex02Flow):
    """
    Use Case id:            NETEX_02
    Slogan:                 Network Explorer Collections
    """

    NAME = "NETEX_02"

    def run(self):
        self.execute_flow()


netex_02 = NETEX_02()
