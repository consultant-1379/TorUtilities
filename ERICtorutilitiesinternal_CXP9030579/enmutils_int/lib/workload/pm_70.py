from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_70(PmStatisticalProfile):
    """
    Use Case ID:    PM_70
    Slogan:         SGB-IS Statistical File Collection
    """
    NAME = "PM_70"

    def run(self):
        self.execute_flow()


pm_70 = PM_70()
