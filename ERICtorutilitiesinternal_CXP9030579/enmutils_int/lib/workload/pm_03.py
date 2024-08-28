from enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile import PmCelltraceProfile


class PM_03(PmCelltraceProfile):
    """
    Use Case ID:        PM_03
    Slogan:             eNodeB DU Radio Node Cell Trace Subscription & File Collection
    """

    NAME = "PM_03"

    def run(self):
        self.execute_flow()


pm_03 = PM_03()
