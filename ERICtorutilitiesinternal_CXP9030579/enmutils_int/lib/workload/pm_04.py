from enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile import PmCelltraceProfile


class PM_04(PmCelltraceProfile):
    """
    Use Case ID:    PM_04
    Slogan:         ERBS Continuous Cell Trace Recording Subscription & File collection Average
    """
    NAME = "PM_04"

    def run(self):
        self.execute_flow()


pm_04 = PM_04()
