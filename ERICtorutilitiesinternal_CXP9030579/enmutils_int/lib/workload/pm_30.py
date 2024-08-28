from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_30(PmStatisticalProfile):
    """
    Use Case ID:        PM_30
    Slogan:             RBS Stats Subscription & File Collection
    """

    NAME = "PM_30"

    def run(self):
        self.execute_flow()


pm_30 = PM_30()
