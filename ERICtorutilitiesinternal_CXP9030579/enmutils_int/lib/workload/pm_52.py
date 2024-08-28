from enmutils_int.lib.profile_flows.pm_flows.pm52profile import Pm52Profile


class PM_52(Pm52Profile):
    """
    Use Case id:        PM_52
    Slogan:             Uplink spectrum file collection & Retention
    """
    NAME = "PM_52"

    def run(self):
        self.execute_flow()


pm_52 = PM_52()
