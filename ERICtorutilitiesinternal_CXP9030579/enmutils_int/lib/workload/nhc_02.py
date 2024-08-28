from enmutils_int.lib.profile_flows.nhc_flows.nhc_02_flow import Nhc02


class NHC_02(Nhc02):
    """
    Use Case id:        NHC_02
    Slogan:             NHC Baseband Radio node node health check.
    """

    NAME = "NHC_02"

    def run(self):
        self.execute_nhc_02_flow()


nhc_02 = NHC_02()
