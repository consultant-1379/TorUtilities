from enmutils_int.lib.profile_flows.fm_flows.fm_12_flow import Fm12


class FM_12(Fm12):
    """
    Use Case ID:        FM_12
    Slogan:             Number of FM NBI interfaces
    """

    NAME = "FM_12"

    def run(self):
        self.execute_flow()


fm_12 = FM_12()
