from enmutils_int.lib.profile_flows.lkf_flows.lkf_01_flow import Lkf01Flow


class LKF_01(Lkf01Flow):
    """
    Use Case id:        LKF_01
    Slogan:             Capacity Expansion
    """
    NAME = "LKF_01"

    def run(self):
        self.execute_flow()


lkf_01 = LKF_01()
