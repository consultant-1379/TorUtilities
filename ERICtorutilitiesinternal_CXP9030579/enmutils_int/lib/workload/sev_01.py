from enmutils_int.lib.profile_flows.sev_flows.sev_flow import SEV01Flow


class SEV_01(SEV01Flow):
    """
    Use Case ID:    SEV_01
    Slogan:    Site Solution Visualization Energy Flow
    """
    NAME = "SEV_01"

    def run(self):
        self.execute_flow()


sev_01 = SEV_01()
