from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_64(PmStatisticalProfile):
    """
    Use Case ID:    PM_64
    Slogan:         MSC-BC-BSP Statistical File Collection
    """
    NAME = "PM_64"

    def run(self):
        self.execute_flow()


pm_64 = PM_64()
