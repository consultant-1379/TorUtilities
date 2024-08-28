from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_91(PmStatisticalProfile):
    """
    Use Case ID:        PM_91
    Slogan:             Router6675 Stats Subscription & File Collection
    """
    NAME = "PM_91"

    def run(self):
        self.execute_flow()


pm_91 = PM_91()
