from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import ReparentingCmImportFlow


class CMIMPORT_27(ReparentingCmImportFlow):
    """
    Use Case ID:    CMIMPORT_27
    Slogan:         Large Standard Create/Delete configuration using Live Config
    """

    NAME = "CMIMPORT_27"

    def run(self):
        self.execute_flow()


cmimport_27 = CMIMPORT_27()
