from enmutils_int.lib.profile_flows.nhm_flows.nhm_08_flow import Nhm08


class NHM_08(Nhm08):
    """
    Use Case ID:            NHM_08
    Slogan:                 Simultaneous Node Monitor Users
    """

    NAME = "NHM_08"

    def run(self):
        self.execute_flow()


nhm_08 = NHM_08()
