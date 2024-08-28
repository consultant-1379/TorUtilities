from enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow import Ftpes01Flow


class FTPES_01(Ftpes01Flow):
    """
    Use Case ID:            FTPES_01
    Slogan:                 FPTES over Explicit TLS
    """
    NAME = "FTPES_01"

    def run(self):
        self.execute_flow()


ftpes_01 = FTPES_01()
