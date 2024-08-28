from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_75(PmStatisticalProfile):
    """
    Use Case ID:    PM_75
    Slogan:         Router 6274 Statistical File Collection
    """
    NAME = "PM_75"

    def run(self):
        self.execute_flow()


pm_75 = PM_75()
