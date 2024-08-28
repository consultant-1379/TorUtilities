from enmutils_int.lib.profile_flows.fm_flows.fm_21_flow import Fm21


class FM_21(Fm21):
    """
    Use Case ID:        FM_21
    Slogan:             Network Alarm Sync
    """
    NAME = "FM_21"

    def run(self):
        self.execute_flow_fm_21()


fm_21 = FM_21()
