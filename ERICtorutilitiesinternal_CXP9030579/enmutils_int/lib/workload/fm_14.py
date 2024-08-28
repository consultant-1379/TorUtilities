from enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow import FmAlarmHistorySearchFlow


class FM_14(FmAlarmHistorySearchFlow):
    """
    Use Case ID:        FM_14
    Slogan:             Number of Alarm History Search users
    """

    NAME = "FM_14"

    def run(self):
        self.execute_flow_fm_alarm_history_search()


fm_14 = FM_14()
