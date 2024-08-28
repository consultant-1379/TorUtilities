from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec13Flow


class NODESEC_13(NodeSec13Flow):
    """
    Use Case ID:            NodeSec_13
    Slogan:                 Trust Distribution and Remove Trust from the node
    """
    NAME = "NODESEC_13"

    def run(self):
        self.execute_flow()


nodesec_13 = NODESEC_13()
