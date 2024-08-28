from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_96(PmStatisticalProfile):
    """
    Use Case ID:      PM_96
    Slogan:           Router6675 Stats Subscription & File Collection.
    """
    NAME = "PM_96"

    def run(self):
        self.execute_flow()


pm_96 = PM_96()
