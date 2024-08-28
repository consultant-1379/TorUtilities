from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_69(PmStatisticalProfile):
    """
    Use Case ID:    PM_69
    Slogan:         Router 6274 Statistical File Collection
    """
    NAME = "PM_69"

    def run(self):
        self.execute_flow()


pm_69 = PM_69()
