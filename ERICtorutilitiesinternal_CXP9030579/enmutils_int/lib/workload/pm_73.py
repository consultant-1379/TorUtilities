from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_73(PmStatisticalProfile):
    """
    Use Case ID:    PM_73
    Slogan:         Fronthaul 6080 Statistical File Collection
    """
    NAME = "PM_73"

    def run(self):
        self.execute_flow()


pm_73 = PM_73()
