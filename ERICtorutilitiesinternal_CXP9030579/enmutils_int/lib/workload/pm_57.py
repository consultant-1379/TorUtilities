from enmutils_int.lib.profile_flows.pm_flows.pm57profile import Pm57Profile


class PM_57(Pm57Profile):
    """
    Use Case ID:        PM_57
    Slogan:             Uplink Spectrum UI
    """
    NAME = "PM_57"

    def run(self):
        self.execute_flow()


pm_57 = PM_57()
