from enmutils_int.lib.profile_flows.netview_flows.netview_02_flow import Netview02Flow


class NETVIEW_02(Netview02Flow):
    """
    Use case id:            NETVIEW_02
    Slogan:                 Network Visualization
    """

    NAME = "NETVIEW_02"

    def run(self):
        self.execute_flow()


netview_02 = NETVIEW_02()
