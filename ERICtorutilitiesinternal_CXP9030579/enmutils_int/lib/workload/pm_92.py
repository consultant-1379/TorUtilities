from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_92(PmStatisticalProfile):
    """
    Use Case ID:        PM_92
    Slogan:             Mini Link 6691 Stats Subscription & File Collection
    """
    NAME = "PM_92"

    def run(self):
        self.execute_flow()


pm_92 = PM_92()
