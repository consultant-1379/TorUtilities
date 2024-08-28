from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_60(PmStatisticalProfile):
    """
    Use Case ID:        PM_60
    Slogan:             RadioNode Stats Subscription & File Collection
    """
    NAME = "PM_60"

    def run(self):
        self.execute_flow()


pm_60 = PM_60()
