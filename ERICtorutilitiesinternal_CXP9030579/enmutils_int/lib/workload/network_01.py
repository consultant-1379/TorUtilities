from enmutils_int.lib.profile_flows.network_flows.network_flow import Network01Flow


class NETWORK_01(Network01Flow):

    """
    Use Case id:        Network_01
    Slogan:             Continuous restart of random nodes
    """
    NAME = "NETWORK_01"

    def run(self):
        self.execute_flow()


network_01 = NETWORK_01()
