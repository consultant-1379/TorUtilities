from enmutils_int.lib.profile_flows.fm_flows.fm_11_flow import Fm11


class FM_11(Fm11):
    """
    Use Case ID:        FM_11
    Slogan:             Max open alarms using ENM CLI
    """
    NAME = "FM_11"

    def run(self):
        self.execute_flow_fm_11()


fm_11 = FM_11()
