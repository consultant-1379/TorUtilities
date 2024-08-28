from enmutils_int.lib.profile_flows.aid_flows.aid_flow import Aid04Flow


class AID_04(Aid04Flow):
    """
    Use Case ID:        AID_04
    Slogan:             AutoID Management Close-Loop Check
    """

    NAME = "AID_04"

    def run(self):
        self.execute_flow()


aid_04 = AID_04()
