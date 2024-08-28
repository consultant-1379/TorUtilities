from enmutils_int.lib.profile_flows.fm_flows.fm_03_flow import Fm03


class FM_03(Fm03):
    """
    Use Case ID:        FM_03
    Slogan:             Storm FM alarm rate alarms/sec
    """

    NAME = "FM_03"

    def run(self):
        self.execute_fm_03_alarm_rate_normal_flow()


fm_03 = FM_03()
