from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_67(PmStatisticalProfile):
    """
    Use Case ID:    PM_67
    Slogan:         CISCO ASR900 Statistical File Collection
    """
    NAME = "PM_67"

    def run(self):
        self.execute_flow()


pm_67 = PM_67()
