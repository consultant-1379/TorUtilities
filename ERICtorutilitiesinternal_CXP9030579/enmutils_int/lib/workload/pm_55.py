from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_55(PmStatisticalProfile):
    """
    Use Case ID:        PM_55
    Slogan:             Mini-Link Outdoor Stats Subscription & File Collection
    """
    NAME = "PM_55"

    def run(self):
        self.execute_flow()


pm_55 = PM_55()
