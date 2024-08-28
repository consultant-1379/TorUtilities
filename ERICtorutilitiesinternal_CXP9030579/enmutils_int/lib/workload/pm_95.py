from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_95(PmStatisticalProfile):
    """
    Use Case ID:        PM_95
    Slogan:             Router6672 Stats Subscription & File Collection
    """
    NAME = "PM_95"

    def run(self):
        self.execute_flow()


pm_95 = PM_95()
