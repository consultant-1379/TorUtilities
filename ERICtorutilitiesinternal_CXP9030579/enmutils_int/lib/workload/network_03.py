from enmutils_int.lib.profile_flows.network_flows.network_flow import Network03Flow


class NETWORK_03(Network03Flow):

    """
    Use Case id:        Network_03
    Slogan:             Reduce bandwidth on MINILINK Indoor nodes and increase latency
    """
    NAME = "NETWORK_03"

    def run(self):
        self.execute_flow()


network_03 = NETWORK_03()
