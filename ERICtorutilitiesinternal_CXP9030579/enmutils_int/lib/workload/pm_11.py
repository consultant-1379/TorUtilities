from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_11(PmStatisticalProfile):
    """
    Use Case ID:    PM_11
    Slogan:         1 subscription containing all ENodeBs, 10% counter.
    """
    NAME = "PM_11"

    def run(self):
        self.execute_offset_flow(profile_to_wait_for='PM_02')


pm_11 = PM_11()
