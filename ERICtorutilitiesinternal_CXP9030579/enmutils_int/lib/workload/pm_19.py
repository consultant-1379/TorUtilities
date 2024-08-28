from enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile import PmUETraceProfile


class PM_19(PmUETraceProfile):
    """
    Use Case ID:    PM_19
    Slogan:         SGSN-MME CTUM File
    """
    NAME = "PM_19"

    def run(self):
        self.execute_flow()


pm_19 = PM_19()
