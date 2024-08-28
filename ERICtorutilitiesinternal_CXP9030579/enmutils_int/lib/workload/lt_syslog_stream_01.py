from enmutils_int.lib.profile_flows.lt_syslog_stream_flows.lt_syslog_stream_flow import LtSysLogStreamFlow


class LT_SYSLOG_STREAM_01(LtSysLogStreamFlow):
    """
    Use Case ID:    LT_SYSLOG_STREAM_01
    Slogan:    Streaming Logs from LT to syslog receiver
    """
    NAME = "LT_SYSLOG_STREAM_01"

    def run(self):
        self.execute_flow()


lt_syslog_stream_01 = LT_SYSLOG_STREAM_01()
