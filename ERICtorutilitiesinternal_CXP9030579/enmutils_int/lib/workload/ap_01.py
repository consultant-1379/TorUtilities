from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap01Flow


class AP_01(Ap01Flow):
    """
    Use Case id:        AP_01
    Slogan:             Create Projects,
                        Download initial Artifacts,
                        Order nodes,
                        Download Order Artifacts,
                        Integrate Nodes,
                        Delete Projects,
                        Remove Nodes.
    """

    NAME = "AP_01"
    EXCLUSIVE = True

    def run(self):
        self.execute_flow()


ap_01 = AP_01()
