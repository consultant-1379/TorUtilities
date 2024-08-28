from enmutils_int.lib.profile_flows.fm_flows.fm_10_flow import Fm10


class FM_10(Fm10):
    """
    Use Case ID:        FM_10
    Slogan:             Acknowledge 1k Alarms in a single batch
    """
    NAME = "FM_10"

    def run(self):
        self.execute_flow_fm_10()


fm_10 = FM_10()
