from enmutils_int.lib.profile_flows.fm_flows.fm_09_flow import Fm09


class FM_09(Fm09):
    """
    Use Case ID:        FM_09
    Slogan:             Passive Users
    """
    NAME = "FM_09"

    def run(self):
        self.execute_flow_fm_09()


fm_09 = FM_09()
