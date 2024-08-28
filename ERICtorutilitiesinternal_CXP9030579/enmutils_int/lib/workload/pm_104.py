from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_104(PmStatisticalProfile):
    """
    Use Case ID:    PM_104
    Slogan:         Shared-CNF(vDU) Stats Subscription & File Collection
    """
    NAME = "PM_104"

    def run(self):
        self.execute_flow()


pm_104 = PM_104()
