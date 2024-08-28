from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_102(PmStatisticalProfile):
    """
    Use Case ID:    PM_102
    Slogan:         Shared-CNF(vCUCP) Stats Subscription & File Collection
    """
    NAME = "PM_102"

    def run(self):
        self.execute_flow()


pm_102 = PM_102()
