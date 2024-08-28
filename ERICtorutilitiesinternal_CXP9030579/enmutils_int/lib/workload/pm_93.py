from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_93(PmStatisticalProfile):
    """
    Use Case ID:        PM_93
    Slogan:             Mini Link 6691 Stats Subscription & File Collection
    """
    NAME = "PM_93"

    def run(self):
        self.execute_flow()


pm_93 = PM_93()
