from enmutils_int.lib.profile_flows.asu_flows.asu_flow import AsuFlow


class ASU_01(AsuFlow):
    """
    Use Case ID:    ASU_01
    Slogan:         Automatic Software Rollout Flow
    """

    NAME = "ASU_01"

    def run(self):
        self.execute_flow()


asu_01 = ASU_01()
