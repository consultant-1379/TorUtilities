from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_54(PmStatisticalProfile):
    """
    Use Case ID:        PM_54
    Slogan:             Mini-Link Indoor Stats Subscription & File Collection
    """
    NAME = "PM_54"

    def run(self):
        self.execute_flow()


pm_54 = PM_54()
