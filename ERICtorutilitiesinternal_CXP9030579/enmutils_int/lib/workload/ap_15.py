from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap15Flow


class AP_15(Ap15Flow):

    """
    Use Case id:        AP_15
    Slogan:             Status project
    """

    NAME = "AP_15"

    def run(self):
        self.execute_flow()


ap_15 = AP_15()
