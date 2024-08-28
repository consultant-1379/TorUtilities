from enmutils_int.lib.profile_flows.netview_flows.netview_01_flow import Netview01Flow


class NETVIEW_01(Netview01Flow):
    """
    Use case id:            NETVIEW_01
    Slogan:                 Network Visualization
    """

    NAME = "NETVIEW_01"

    def run(self):
        self.execute_flow()


netview_01 = NETVIEW_01()
