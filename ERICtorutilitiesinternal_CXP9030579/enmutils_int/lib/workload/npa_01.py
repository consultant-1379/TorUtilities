from enmutils_int.lib.profile_flows.npa_flows.npa_flow import Npa01Flow


class NPA_01(Npa01Flow):
    """
    Use Case ID:    NPA_01
    Slogan:         Network Performance Acceptance
    """

    NAME = "NPA_01"

    def run(self):
        self.execute_flow()


npa_01 = NPA_01()
