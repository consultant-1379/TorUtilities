from enmutils_int.lib.profile_flows.netex_flows.netex_flow import Netex04Flow


class NETEX_04(Netex04Flow):
    """
    Use case id:            NETEX_04
    Slogan:                 Create/Update collections from a file
    """

    NAME = "NETEX_04"

    def run(self):
        self.execute_flow()


netex_04 = NETEX_04()
