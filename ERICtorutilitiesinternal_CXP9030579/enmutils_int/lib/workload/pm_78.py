from enmutils_int.lib.profile_flows.pm_flows.pmmtrprofile import PmMtrProfile


class PM_78(PmMtrProfile):
    """
    Use Case ID:    PM_78
    Slogan:         GSM MTR subscription
    """
    NAME = "PM_78"

    def run(self):
        self.execute_flow()


pm_78 = PM_78()
