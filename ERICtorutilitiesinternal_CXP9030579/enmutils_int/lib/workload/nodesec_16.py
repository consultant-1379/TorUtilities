from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow import NodeSec16Flow


class NODESEC_16(NodeSec16Flow):
    """
    Use Case ID:            NodeSec_16
    Slogan:                 Renew LDAP proxy accounts for 1000 nodes and create 1000 spare proxy accounts
    """
    NAME = "NODESEC_16"

    def run(self):
        self.execute_flow()


nodesec_16 = NODESEC_16()
