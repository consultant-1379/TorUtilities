from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_32(PmStatisticalProfile):
    """
    Use Case ID:        PM_32
    Slogan:             Router6000 Stats Subscription & File Collection
    """
    NAME = "PM_32"

    def run(self):
        self.execute_flow()


pm_32 = PM_32()
