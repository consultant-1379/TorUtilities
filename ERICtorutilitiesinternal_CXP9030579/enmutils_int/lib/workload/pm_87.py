from enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile import PmCelltraceProfile


class PM_87(PmCelltraceProfile):
    """
    Use Case ID:        PM_87
    Slogan:             5G gNodeB Low Priority Continuous Cell Trace Subscription.
    """

    NAME = "PM_87"

    def run(self):
        self.execute_flow()


pm_87 = PM_87()
