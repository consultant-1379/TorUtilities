from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_88(PmStatisticalProfile):
    """
    Use Case ID:    PM_88
    Slogan:         Fronthaul 6020 Statistical Subscription and File Collection
    """
    NAME = "PM_88"

    def run(self):
        self.execute_flow()


pm_88 = PM_88()
