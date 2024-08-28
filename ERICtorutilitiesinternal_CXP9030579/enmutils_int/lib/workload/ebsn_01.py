from enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile import EBSN01Profile


class EBSN_01(EBSN01Profile):
    """
    Use Case ID:    EBS-N_01
    Slogan:         EBS-N File-based Subscription
    """

    NAME = "EBSN_01"

    def run(self):
        self.execute_flow()


ebsn_01 = EBSN_01()
