from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_85(PmStatisticalProfile):
    """
    Use Case ID:    PM_85
    Slogan:         DSC Stats Subscription & file Collection
    """
    NAME = "PM_85"

    def run(self):
        self.execute_flow()


pm_85 = PM_85()
