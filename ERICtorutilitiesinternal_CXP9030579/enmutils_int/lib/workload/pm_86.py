from enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile import PmCelltraceProfile


class PM_86(PmCelltraceProfile):
    """
    Use Case ID:    PM_86
    Slogan:         5G gNodeB High Priority Continuous Cell Trace Subscription.
    """
    NAME = "PM_86"

    def run(self):
        self.execute_flow()


pm_86 = PM_86()
