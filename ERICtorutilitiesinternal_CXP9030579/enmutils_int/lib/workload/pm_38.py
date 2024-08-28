from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_38(PmStatisticalProfile):
    """
    Use Case ID:    PM_38
    Slogan:         RadioNode Stats Subscription & File Collection
    """
    NAME = "PM_38"

    def run(self):
        self.execute_flow()


pm_38 = PM_38()
