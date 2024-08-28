from enmutils_int.lib.profile_flows.pkiadmin_flows.pkiadmin_flow import PkiAdmin01Flow


class PKIADMIN_01(PkiAdmin01Flow):
    """
    Use Case ID:            PKIAdmin_01
    Slogan:                 PKIAdmin
    """
    NAME = "PKIADMIN_01"

    def run(self):
        self.execute_flow()


pkiadmin_01 = PKIADMIN_01()
