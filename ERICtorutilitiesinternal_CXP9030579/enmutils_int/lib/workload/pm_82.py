from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_82(PmStatisticalProfile):
    """
    Use Case ID:        PM_82
    Slogan:             Juniper Stats Subscription & File Collection
    """
    NAME = "PM_82"

    def run(self):
        self.execute_flow()


pm_82 = PM_82()
