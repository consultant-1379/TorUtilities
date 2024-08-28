from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_25(PmStatisticalProfile):
    """
    Use Case ID:    PM_25
    Slogan:         MGW Stats Subscription & file Collection
    """
    NAME = "PM_25"

    def run(self):
        self.execute_flow()


pm_25 = PM_25()
