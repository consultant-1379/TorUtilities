from enmutils_int.lib.profile_flows.fm_flows.fm_01_flow import Fm01


class FM_01(Fm01):
    """
    Use Case ID:        FM_01
    Slogan:             Normal FM alarm rate alarms/sec
    """

    NAME = "FM_01"

    def run(self):
        self.execute_fm_01_alarm_rate_normal_flow()


fm_01 = FM_01()
