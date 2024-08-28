from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_90(PmStatisticalProfile):
    """
    Use Case ID:    PM_90
    Slogan:         Router6675 Stats Subscription & File Collection.
    """
    NAME = "PM_90"

    def run(self):
        self.execute_flow()


pm_90 = PM_90()
