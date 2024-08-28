from enmutils_int.lib.profile_flows.fm_flows.fm_27_flow import Fm27


class FM_27(Fm27):
    """
    Use case id:            FM_27
    Slogan:                 Alarm Routing Save To File
    """

    NAME = "FM_27"

    def run(self):
        self.execute_flow()


fm_27 = FM_27()
