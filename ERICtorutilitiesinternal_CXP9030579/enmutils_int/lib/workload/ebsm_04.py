from enmutils_int.lib.profile_flows.ebsm_flows.ebsm_flow import EBSM04Profile


class EBSM_04(EBSM04Profile):
    """
    Use Case ID:    EBS-M_04
    Slogan:         EBM Subscription
    """

    NAME = "EBSM_04"

    def run(self):
        self.execute_flow()


ebsm_04 = EBSM_04()
