from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec15Flow


class NODESEC_15(NodeSec15Flow):
    """
    Use Case ID:            NodeSec_15
    Slogan:                 get Credentials
    """
    NAME = "NODESEC_15"

    def run(self):
        self.execute_flow()


nodesec_15 = NODESEC_15()
