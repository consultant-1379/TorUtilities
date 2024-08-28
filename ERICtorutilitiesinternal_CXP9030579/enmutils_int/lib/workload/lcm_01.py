from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class LCM_01(PlaceHolderFlow):
    """
    Use Case ID:        LCM_01
    Slogan:             Node License check
    """
    NAME = "LCM_01"

    def run(self):
        self.execute_flow()


lcm_01 = LCM_01()
