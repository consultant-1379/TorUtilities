from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_103(PmStatisticalProfile):
    """
    Use Case ID:    PM_103
    Slogan:         Shared-CNF(vCUUP) Stats Subscription & File Collection
    """
    NAME = "PM_103"

    def run(self):
        self.execute_flow()


pm_103 = PM_103()
