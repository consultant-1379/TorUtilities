from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_83(PmStatisticalProfile):
    """
    Use Case ID:        PM_83
    Slogan:             Juniper Stats Subscription & File Collection
    """
    NAME = "PM_83"

    def run(self):
        self.execute_flow()


pm_83 = PM_83()
