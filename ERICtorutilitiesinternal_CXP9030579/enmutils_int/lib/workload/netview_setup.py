from enmutils_int.lib.profile_flows.netview_flows.netview_setup_flow import NetviewSetupFlow


class NETVIEW_SETUP(NetviewSetupFlow):
    """
    Use case id:            NETVIEW_SETUP
    Slogan:                 Network Visualization
    """

    NAME = "NETVIEW_SETUP"

    def run(self):
        self.execute_flow()


netview_setup = NETVIEW_SETUP()
