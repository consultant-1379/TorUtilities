from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import NodeSec08Flow


class NODESEC_08(NodeSec08Flow):
    """
    Use Case ID:            NodeSec_08
    Slogan:                 SNMP Configuration for 900 nodes
    """
    NAME = "NODESEC_08"

    def run(self):
        self.execute_flow()


nodesec_08 = NODESEC_08()
