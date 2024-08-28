from enmutils_int.lib.profile_flows.pm_flows.pm_49_flow import Pm49Flow


class PM_49(Pm49Flow):
    """
    Use Case ID:        PM_49
    Slogan:             PushService
    """
    NAME = "PM_49"

    def run(self):
        self.execute_flow()


pm_49 = PM_49()
