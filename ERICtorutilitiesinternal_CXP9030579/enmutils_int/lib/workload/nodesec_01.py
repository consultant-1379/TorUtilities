from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec01Flow


class NODESEC_01(NodeSec01Flow):
    """
    Use Case ID:            NodeSec_01
    Slogan:                 Remove and Create Credentials for 1000 nodes
    """
    NAME = "NODESEC_01"

    def run(self):
        self.execute_flow()


nodesec_01 = NODESEC_01()
