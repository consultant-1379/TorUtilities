from enmutils_int.lib.profile_flows.fm_flows.fm_26_flow import Fm26


class FM_26(Fm26):
    """
    Use case id:            FM_26
    Slogan:                 ENM CLI alarm history capability
    """

    NAME = "FM_26"

    def run(self):
        self.alarm_history_cli_capability_main_flow()


fm_26 = FM_26()
