from enmutils_int.lib.profile_flows.ap_flows.ap_flow import ApSetupFlow


class AP_SETUP(ApSetupFlow):
    """
    Pre-requisite to running Profiles: AP 11 - 16
    """

    NAME = "AP_SETUP"

    def run(self):
        self.execute_flow()


ap_setup = AP_SETUP()
