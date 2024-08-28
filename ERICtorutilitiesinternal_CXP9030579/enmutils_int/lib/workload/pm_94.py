from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_94(PmStatisticalProfile):
    """
    Use Case ID:    PM_94
    Slogan:         EPG-OI Stats Subscription & File Collection
    """
    NAME = "PM_94"

    def run(self):
        self.execute_flow()


pm_94 = PM_94()
