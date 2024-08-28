from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_98(PmStatisticalProfile):
    """
    Use Case ID:    PM_98
    Slogan:         PCG Stats Subscription & File Collection
    """
    NAME = "PM_98"

    def run(self):
        self.execute_flow()


pm_98 = PM_98()
