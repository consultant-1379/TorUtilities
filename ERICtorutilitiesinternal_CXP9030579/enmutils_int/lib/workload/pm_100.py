from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_100(PmStatisticalProfile):
    """
    Use Case ID:      PM_100
    Slogan:           CUDB Stats Subscription & File Collection.
    """
    NAME = "PM_100"

    def run(self):
        self.execute_flow()


pm_100 = PM_100()
