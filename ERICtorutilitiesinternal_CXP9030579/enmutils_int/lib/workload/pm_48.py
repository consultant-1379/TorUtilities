from enmutils_int.lib.profile_flows.pm_flows.pmstatisticalprofile import PmStatisticalProfile


class PM_48(PmStatisticalProfile):
    """
    Use Case ID:    PM_48
    Slogan:         1 subscription containing all ENodeBs, 10% counters.
    """
    NAME = "PM_48"

    def run(self):
        self.execute_offset_flow(profile_to_wait_for='PM_38')


pm_48 = PM_48()
