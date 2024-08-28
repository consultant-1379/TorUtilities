from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec03Flow


class NODESEC_03(NodeSec03Flow):
    """
    Use Case ID:            NodeSec_03
    Slogan:                 Change Node security from SL1 to SL2
    """
    NAME = "NODESEC_03"

    def run(self):
        self.execute_flow()


nodesec_03 = NODESEC_03()
