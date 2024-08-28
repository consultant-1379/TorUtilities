from enmutils_int.lib.profile_flows.asrn_flows.asrn_flow import ASRN01Profile


class ASR_N_01(ASRN01Profile):
    """
    Use Case ID:    ASR-N 01
    Slogan:         ASR-N Configuration and Subscription
    """

    NAME = "ASR_N_01"

    def run(self):
        self.execute_flow()


asr_n_01 = ASR_N_01()
