from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_68(PmStatisticalProfile):
    """
    Use Case ID:    PM_68
    Slogan:         Fronthaul 6080 Statistical File Collection
    """
    NAME = "PM_68"

    def run(self):
        self.execute_flow()


pm_68 = PM_68()
