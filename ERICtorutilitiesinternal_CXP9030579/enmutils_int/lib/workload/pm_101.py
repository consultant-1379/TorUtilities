from enmutils_int.lib.profile_flows.pm_flows.pm101profile import Pm101Profile


class PM_101(Pm101Profile):
    """
    Use Case ID:        PM_101
    Slogan:             Updates Retention Periods for pmicCelltraceFileRetentionPeriodInMinutes,
                        pmicEbmFileRetentionPeriodInMinutes pib parameters in ENM
    """

    NAME = "PM_101"

    def run(self):
        self.execute_flow()


pm_101 = PM_101()
