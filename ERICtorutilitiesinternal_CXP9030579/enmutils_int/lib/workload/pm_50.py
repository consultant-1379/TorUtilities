from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_50(PmStatisticalProfile):
    """
    Use Case ID:    PM_50
    Slogan:         MTAS Stats Subscription & file Collection
    """
    NAME = "PM_50"

    def run(self):
        self.execute_flow()


pm_50 = PM_50()
