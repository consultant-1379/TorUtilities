from enmutils_int.lib.profile_flows.ap_flows.ap_flow import Ap14Flow


class AP_14(Ap14Flow):

    """
    Use Case id:        AP_14
    Slogan:             Status all
    """

    NAME = "AP_14"

    def run(self):
        self.execute_flow()


ap_14 = AP_14()
