from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_65(PmStatisticalProfile):
    """
    Use Case ID:    PM_64
    Slogan:         MSC-BC-IS Statistical File Collection
    """
    NAME = "PM_65"

    def run(self):
        self.execute_flow()


pm_65 = PM_65()
