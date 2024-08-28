from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_31(PmStatisticalProfile):
    """
    Use Case ID:        PM_31
    Slogan:             RNC Stats Subscription & File Collection
    """

    NAME = "PM_31"

    def run(self):
        self.execute_flow()


pm_31 = PM_31()
