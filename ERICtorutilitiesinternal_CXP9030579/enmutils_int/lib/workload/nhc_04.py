from enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow import Nhc04


class NHC_04(Nhc04):
    """
    Use Case id:        NHC_04
    Slogan:             NHC Baseband RadioNodes node health check.
    """

    NAME = "NHC_04"

    def run(self):
        self.execute_nhc_04_flow()


nhc_04 = NHC_04()
