from enmutils_int.lib.profile_flows.pm_flows.pm17profile import Pm17Profile


class PM_17(Pm17Profile):
    """
    Use Case ID:        PM_17
    Slogan:             Retention Periods
    """

    NAME = "PM_17"

    def run(self):
        self.execute_flow()


pm_17 = PM_17()
