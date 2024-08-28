from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_58(PmStatisticalProfile):
    """
    Use Case ID:        PM_58
    Slogan:             TCU02 Statistical file Collection
    """
    NAME = "PM_58"

    def run(self):
        self.execute_flow()


pm_58 = PM_58()
