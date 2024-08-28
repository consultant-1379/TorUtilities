from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_84(PmStatisticalProfile):
    """
    Use Case ID:    PM_84
    Slogan:         MTAS Stats Subscription & file Collection
    """
    NAME = "PM_84"

    def run(self):
        self.execute_flow()


pm_84 = PM_84()
