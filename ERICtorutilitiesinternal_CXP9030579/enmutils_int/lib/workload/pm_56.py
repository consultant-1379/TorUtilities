from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_56(PmStatisticalProfile):
    """
    Use Case ID:        PM_56
    Slogan:             SIU02 Statistical file Collection
                        TCU02 Statistical file Collection
    """
    NAME = "PM_56"

    def run(self):
        self.execute_flow()


pm_56 = PM_56()
