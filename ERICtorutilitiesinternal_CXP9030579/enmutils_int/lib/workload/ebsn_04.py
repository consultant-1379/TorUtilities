from enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile import EBSN04Profile


class EBSN_04(EBSN04Profile):
    """
    Use Case ID:    EBS-N_04
    Slogan:         EBS-N File-based Subscription using Flexible Counters
    """

    NAME = "EBSN_04"

    def run(self):
        self.execute_flow()


ebsn_04 = EBSN_04()
