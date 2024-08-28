from enmutils_int.lib.profile_flows.fm_flows.fm_25_flow import Fm25


class FM_25(Fm25):
    """
    Use Case ID:        FM_25
    Slogan:             Network Log Management
    """
    NAME = "FM_25"

    def run(self):
        self.execute_flow_fm_25()


fm_25 = FM_25()
