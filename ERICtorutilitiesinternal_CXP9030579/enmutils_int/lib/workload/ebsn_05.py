from enmutils_int.lib.profile_flows.ebsn_flows.ebsnprofile import EBSN05Profile


class EBSN_05(EBSN05Profile):
    """
    Use Case ID:    EBS-N_05
    Slogan:         EBS-N Stream-based Subscription using Flexible Counters
    """

    NAME = "EBSN_05"

    def run(self):
        self.execute_flow()


ebsn_05 = EBSN_05()
