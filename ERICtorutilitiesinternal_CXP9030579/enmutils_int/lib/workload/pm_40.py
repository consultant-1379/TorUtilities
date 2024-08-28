from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_40(PmStatisticalProfile):
    """
    Use Case ID:    PM_40
    Slogan:         SGSN MME Stats Subscription & File Collection
    """
    NAME = "PM_40"

    def run(self):
        self.execute_flow()


pm_40 = PM_40()
