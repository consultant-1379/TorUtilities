from enmutils_int.lib.profile_flows.pm_flows.pm79profile import Pm79Profile


class PM_79(Pm79Profile):

    """
    Use Case id:        PM_79
    Slogan:             Uplink Spectrum Scheduled Sampling.
    """

    NAME = "PM_79"

    def run(self):
        self.execute_flow()


pm_79 = PM_79()
