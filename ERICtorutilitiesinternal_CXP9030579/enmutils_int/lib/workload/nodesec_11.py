from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec11Flow


class NODESEC_11(NodeSec11Flow):
    """
    Use Case ID:            NodeSec_11
    Slogan:                 Issue/Reissue Node Certificates
    """
    NAME = "NODESEC_11"

    def run(self):
        self.execute_flow()


nodesec_11 = NODESEC_11()
