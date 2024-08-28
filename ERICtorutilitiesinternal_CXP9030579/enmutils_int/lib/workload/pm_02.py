from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_02(PmStatisticalProfile):
    """
    Use Case ID:    PM_02
    Slogan:         ERBS Stats CBS Subscription & File Collection
    """
    NAME = "PM_02"

    def run(self):
        self.execute_flow()


pm_02 = PM_02()
