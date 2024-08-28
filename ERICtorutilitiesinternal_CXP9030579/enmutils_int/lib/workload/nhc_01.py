from enmutils_int.lib.profile_flows.nhc_flows.nhc_01_flow import Nhc01


class NHC_01(Nhc01):
    """
    Use Case id:        NHC_01
    Slogan:             Daily Node Health Check.
    """

    NAME = "NHC_01"

    def run(self):
        self.execute_nhc_01_flow()


nhc_01 = NHC_01()
