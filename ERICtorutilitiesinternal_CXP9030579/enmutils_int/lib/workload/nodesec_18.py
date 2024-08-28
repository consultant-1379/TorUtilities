from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec18Flow


class NODESEC_18(NodeSec18Flow):
    """
    Use Case ID:            NodeSec_18
    Slogan:                 SSHKEY Create and Delete on SGSN-MME nodes.
    """
    NAME = "NODESEC_18"

    def run(self):
        self.execute_flow()


nodesec_18 = NODESEC_18()
