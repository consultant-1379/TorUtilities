from enmutils_int.lib.profile_flows.ebsl_flows.ebslprofile import EBSL05Profile


class EBSL_05(EBSL05Profile):
    """
    Use Case ID:    EBS-L_05
    Slogan:         EBS-L File-based Subscription
    """

    NAME = "EBSL_05"

    def run(self):
        self.execute_flow(netex_query="select networkelement where neType=ERBS or neType=RadioNode and "
                                      "managedelement has child eNodeBFunction and"
                                      " managedelement has child NodeBFunction")


ebsl_05 = EBSL_05()
