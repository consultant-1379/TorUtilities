from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_59(PmStatisticalProfile):
    """
    Use Case ID:        PM_59
    Slogan:             ERBS Stats Subscription & File Collection
    """
    NAME = "PM_59"

    def run(self):
        self.execute_flow()


pm_59 = PM_59()
