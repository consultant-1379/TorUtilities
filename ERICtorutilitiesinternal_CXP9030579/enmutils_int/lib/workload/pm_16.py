from enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile import PmUETraceProfile


class PM_16(PmUETraceProfile):
    """
    Use Case ID:    PM_16
    Slogan:         ERBS UETrace File Collection Average
    """
    NAME = "PM_16"

    def run(self):
        self.execute_flow()


pm_16 = PM_16()
