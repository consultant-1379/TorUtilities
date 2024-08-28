from enmutils_int.lib.profile_flows.sev_flows.sev_flow import SEV02Flow


class SEV_02(SEV02Flow):
    """
    Use Case ID:    SEV_02
    Slogan:    Site Solution Visualization Energy Report
    """
    NAME = "SEV_02"

    def run(self):
        self.execute_flow()


sev_02 = SEV_02()
