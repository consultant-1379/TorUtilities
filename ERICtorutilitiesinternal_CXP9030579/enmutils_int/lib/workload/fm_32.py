from enmutils_int.lib.profile_flows.fm_flows.fm_32_flow import Fm32


class FM_32(Fm32):
    """
    Use Case ID:        FM_32
    Slogan:             FM Storm Overload
    """

    NAME = "FM_32"

    def run(self):
        self.execute_fm_32_alarm_flow()


fm_32 = FM_32()
