from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_27(PmStatisticalProfile):
    """
    Use Case ID:    PM_27
    Slogan:         EPG Stats Subscription & file Collection
    """
    NAME = "PM_27"

    def run(self):
        self.execute_flow()


pm_27 = PM_27()
