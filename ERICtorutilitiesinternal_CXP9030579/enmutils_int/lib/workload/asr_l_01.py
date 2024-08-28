from enmutils_int.lib.profile_flows.asr_flows.asrl_flow import ASRL01Profile


class ASR_L_01(ASRL01Profile):
    """
    Use Case ID:    ASR-L_01
    Slogan:         ASR-L Configuration & Subscription
    """

    NAME = "ASR_L_01"

    def run(self):
        self.execute_flow()


asr_l_01 = ASR_L_01()
