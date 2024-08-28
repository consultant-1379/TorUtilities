from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap13Flow


class AP_13(Ap13Flow):

    """
    Use Case id:        AP_13
    Slogan:             View specific nodes
    """

    NAME = "AP_13"

    def run(self):
        self.execute_flow()


ap_13 = AP_13()
