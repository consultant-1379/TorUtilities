from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_72(PmStatisticalProfile):
    """
    Use Case ID:        PM_72
    Slogan:             Mini-Link Outdoor Stats Subscription & File Collection
    """
    NAME = "PM_72"

    def run(self):
        self.execute_flow()


pm_72 = PM_72()
