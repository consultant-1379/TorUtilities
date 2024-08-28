from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap16Flow


class AP_16(Ap16Flow):

    """
    Use Case id:        AP_16
    Slogan:             View all projects
    """

    NAME = "AP_16"

    def run(self):
        self.execute_flow()


ap_16 = AP_16()
