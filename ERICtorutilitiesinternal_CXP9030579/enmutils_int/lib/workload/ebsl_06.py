from enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile import EBSL06Profile


class EBSL_06(EBSL06Profile):
    """
    Use Case ID:    EBS-L_06
    Slogan:         EBS-L Stream-based Subscription
    """
    NAME = "EBSL_06"

    def run(self):
        self.execute_flow()


ebsl_06 = EBSL_06()
