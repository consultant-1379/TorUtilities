from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_99(PmStatisticalProfile):
    """
    Use Case ID:      PM_99
    Slogan:           SCU Stats Subscription & File Collection.
    """
    NAME = "PM_99"

    def run(self):
        self.execute_flow()


pm_99 = PM_99()
