from enmutils_int.lib.profile_flows.fm_flows.fm_02_flow import Fm02


class FM_02(Fm02):
    """
    Use Case ID:        FM_02
    Slogan:             Peak FM alarm rate alarms/sec
    """

    NAME = "FM_02"

    def run(self):
        self.execute_fm_02_alarm_rate_normal_flow()


fm_02 = FM_02()
