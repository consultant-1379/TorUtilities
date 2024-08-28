from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_71(PmStatisticalProfile):
    """
    Use Case ID:        PM_71
    Slogan:             Mini-Link Indoor Stats Subscription & File Collection
    """
    NAME = "PM_71"

    def run(self):
        self.execute_flow()


pm_71 = PM_71()
