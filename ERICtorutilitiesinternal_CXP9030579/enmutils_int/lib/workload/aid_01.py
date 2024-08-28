from enmutils_int.lib.profile_flows.aid_flows.aid_flow import Aid01Flow


class AID_01(Aid01Flow):
    """
    Use Case ID:        AID_01
    Slogan:             Simultaneous Users
    """

    NAME = "AID_01"

    def run(self):
        self.execute_flow()


aid_01 = AID_01()
