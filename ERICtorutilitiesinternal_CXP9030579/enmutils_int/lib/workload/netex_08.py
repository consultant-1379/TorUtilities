from enmutils_int.lib.profile_flows.netex_flows.netex_08_flow import Netex08Flow


class NETEX_08(Netex08Flow):
    """
    Use Case ID:           NETEX_08
    Slogan:                Read of YANG Nodes (cRAN vCUCP) via Networkexplorer
    """
    NAME = "NETEX_08"

    def run(self):
        self.execute_flow()


netex_08 = NETEX_08()
