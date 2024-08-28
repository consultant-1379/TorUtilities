from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec04Flow


class NODESEC_04(NodeSec04Flow):
    """
    Use Case ID:            NodeSec_04
    Slogan:                 Change Node security from SL2 to SL1
    """
    NAME = "NODESEC_04"

    def run(self):
        self.execute_flow()


nodesec_04 = NODESEC_04()
