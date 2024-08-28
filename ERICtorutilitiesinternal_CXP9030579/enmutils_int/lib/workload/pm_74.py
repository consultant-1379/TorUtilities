from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_74(PmStatisticalProfile):
    """
    Use Case ID:    PM_74
    Slogan:         Router6672 Statistical File Collection
    """
    NAME = "PM_74"

    def run(self):
        self.execute_flow()


pm_74 = PM_74()
