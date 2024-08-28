from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_66(PmStatisticalProfile):
    """
    Use Case ID:    PM_66
    Slogan:         ESC Statistical File Collection
    """
    NAME = "PM_66"

    def run(self):
        self.execute_flow()


pm_66 = PM_66()
