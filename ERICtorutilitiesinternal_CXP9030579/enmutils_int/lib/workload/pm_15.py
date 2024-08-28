from enmutils_int.lib.profile_flows.pm_flows.pm15profile import Pm15Profile


class PM_15(Pm15Profile):
    """
    Use Case ID:    PM_15
    Slogan:         Scanner Polling & Master
    """
    NAME = "PM_15"

    def run(self):
        self.execute_flow()


pm_15 = PM_15()
