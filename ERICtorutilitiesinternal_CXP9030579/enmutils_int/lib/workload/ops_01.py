from enmutils_int.lib.profile_flows.ops_flows.ops_01_flow import Ops01Flow


class OPS_01(Ops01Flow):
    """
    Use Case id:        OPS_01
    Slogan:             OPS CLI Sessions
    """
    NAME = "OPS_01"

    def run(self):
        self.execute_flow()


ops_01 = OPS_01()
