from enmutils_int.lib.profile_flows.cbrs_flows.cbrs_setup_flow import CbrsSetupFlow


class CBRS_SETUP(CbrsSetupFlow):
    """
    Use Case id:        CBRS_SETUP
    Slogan:             CBRS Domain Proxy initial setup
    """

    def run(self):
        self.execute_flow()


cbrs_setup = CBRS_SETUP()
