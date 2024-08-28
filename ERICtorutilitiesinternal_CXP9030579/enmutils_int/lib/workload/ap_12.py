from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap12Flow


class AP_12(Ap12Flow):

    """
    Use Case id:        AP_12
    Slogan:             View specific project
    """

    NAME = "AP_12"

    def run(self):
        self.execute_flow()


ap_12 = AP_12()
