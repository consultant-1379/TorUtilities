from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_89(PmStatisticalProfile):
    """
    Use Case ID:    PM_89
    Slogan:         FrontHaul 6020 Stats Subscription and File Collection
    """
    NAME = "PM_89"

    def run(self):
        self.execute_flow()


pm_89 = PM_89()
