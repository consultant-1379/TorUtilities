from enmutils_int.lib.profile_flows.network_flows.network_flow import Network02Flow


class NETWORK_02(Network02Flow):

    """
    Use Case id:        Network_02
    Slogan:             Stop nodes for 10 minutes and restart
    """
    NAME = "NETWORK_02"

    def run(self):
        self.execute_flow()


network_02 = NETWORK_02()
