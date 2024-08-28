from enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow import FmAlarmHistorySearchFlow


class FM_17(FmAlarmHistorySearchFlow):
    """
    Use case id:            FM_17
    Slogan:                 Number of Max Alarm History search users (daily)
    """
    NAME = "FM_17"

    def run(self):
        self.execute_flow_fm_alarm_history_search()


fm_17 = FM_17()
