from enmutils_int.lib.profile_flows.fm_flows.fm_31_flow import Fm31


class FM_31(Fm31):
    """
    Use Case ID:        FM_31
    Slogan:             Default configuration confirmation
    """

    NAME = "FM_31"

    def run(self):
        self.execute_flow()


fm_31 = FM_31()
