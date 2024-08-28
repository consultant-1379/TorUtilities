from enmutils_int.lib.profile_flows.aid_flows.aid_flow import Aid03Flow


class AID_03(Aid03Flow):
    """
    Use Case ID:        AID_03
    Slogan:             AutoID Management Open Loop Check
    """

    NAME = "AID_03"

    def run(self):
        self.execute_flow()


aid_03 = AID_03()
