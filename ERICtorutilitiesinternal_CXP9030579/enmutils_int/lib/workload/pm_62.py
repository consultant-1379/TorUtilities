from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_62(PmStatisticalProfile):
    """
    Use Case ID:    PM_62
    Slogan:         BSC Statistical File Collection
    """
    NAME = "PM_62"

    def run(self):
        self.execute_flow()


pm_62 = PM_62()
