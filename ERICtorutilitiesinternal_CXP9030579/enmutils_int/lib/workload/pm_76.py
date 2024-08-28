from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_76(PmStatisticalProfile):
    """
    Use Case ID:    PM_76
    Slogan:         CISCO ASR900 Statistical File Collection
    """
    NAME = "PM_76"

    def run(self):
        self.execute_flow()


pm_76 = PM_76()
