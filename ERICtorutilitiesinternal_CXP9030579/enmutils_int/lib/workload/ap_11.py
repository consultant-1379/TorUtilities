from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap11Flow


class AP_11(Ap11Flow):

    """
    Use Case id:        AP_11
    Slogan:             View all projects
    """

    NAME = "AP_11"

    def run(self):
        self.execute_flow()


ap_11 = AP_11()
