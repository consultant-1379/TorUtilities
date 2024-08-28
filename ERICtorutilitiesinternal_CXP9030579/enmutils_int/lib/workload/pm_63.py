from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_63(PmStatisticalProfile):
    """
    Use Case ID:    PM_63
    Slogan:         MSC-DB-BSP Statistical File Collection
    """
    NAME = "PM_63"

    def run(self):
        self.execute_flow()


pm_63 = PM_63()
