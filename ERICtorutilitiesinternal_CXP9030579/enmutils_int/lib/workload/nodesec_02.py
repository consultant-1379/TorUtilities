from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec02Flow


class NODESEC_02(NodeSec02Flow):
    """
    Use Case ID:            NodeSec_02
    Slogan:                 Update Credentials for 500 nodes
    """
    NAME = "NODESEC_02"

    def run(self):
        self.execute_flow()


nodesec_02 = NODESEC_02()
