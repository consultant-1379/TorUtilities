from enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile import EBSN03Profile


class EBSN_03(EBSN03Profile):
    """
    Use Case ID:    EBS-N_03
    Slogan:         EBS-N Stream-based Subscription
    """

    NAME = "EBSN_03"

    def run(self):
        self.execute_flow()


ebsn_03 = EBSN_03()
