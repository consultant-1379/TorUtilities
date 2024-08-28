from enmutils_int.lib.profile_flows.fm_flows.fm_08_flow import Fm08


class FM_08(Fm08):
    """
    Use Case ID:        FM_08
    Slogan:             Active Users
    """
    NAME = "FM_08"

    def run(self):
        self.execute_flow_fm_08()


fm_08 = FM_08()
