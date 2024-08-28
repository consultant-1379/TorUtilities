from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow import NodeSec17Flow


class NODESEC_17(NodeSec17Flow):
    """
    Use Case ID:            NodeSec_17
    Slogan:                 Cleanup of Inactive Proxy accounts
    """
    NAME = "NODESEC_17"

    def run(self):
        self.execute_flow()


nodesec_17 = NODESEC_17()
