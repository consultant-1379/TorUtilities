from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_97(PmStatisticalProfile):
    """
    Use Case ID:        PM_97
    Slogan:             CCDM Stats Subscription & File Collection
    """
    NAME = "PM_97"

    def run(self):
        self.execute_flow()


pm_97 = PM_97()
