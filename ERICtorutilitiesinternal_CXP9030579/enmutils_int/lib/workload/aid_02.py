from enmutils_int.lib.profile_flows.aid_flows.aid_flow import Aid02Flow


class AID_02(Aid02Flow):
    """
    Use Case ID:        AID_02
    Slogan:             Manual Check, Calculate and Resolve
    """

    NAME = "AID_02"

    def run(self):
        self.execute_flow()


aid_02 = AID_02()
