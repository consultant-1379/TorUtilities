from enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow import FmAlarmHistorySearchFlow


class FM_15(FmAlarmHistorySearchFlow):
    """
        Use Case ID:        FM_15
        Slogan:             Active Users
        """
    NAME = "FM_15"

    def run(self):

        self.execute_flow_fm_alarm_history_search()


fm_15 = FM_15()
