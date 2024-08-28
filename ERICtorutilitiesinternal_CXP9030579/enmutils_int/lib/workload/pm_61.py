from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_61(PmStatisticalProfile):
    """
    Use Case ID:    PM_61
    Slogan:         DSC Statistical File Collection
    """
    NAME = "PM_61"

    def run(self):
        self.execute_flow()


pm_61 = PM_61()
