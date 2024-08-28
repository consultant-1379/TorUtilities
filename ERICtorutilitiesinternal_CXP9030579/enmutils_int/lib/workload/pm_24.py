from enmutils_int.lib.profile_flows.pm_flows.pmuetraceprofile import PmUETraceProfile


class PM_24(PmUETraceProfile):
    """
    Use Case ID:    PM_24
    Slogan:         SGSN-MME UETrace Subscription & File Collection
    """
    NAME = "PM_24"

    def run(self):
        self.execute_flow()


pm_24 = PM_24()
