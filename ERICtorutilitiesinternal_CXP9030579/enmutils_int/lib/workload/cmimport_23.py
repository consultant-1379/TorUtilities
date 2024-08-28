from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImport23Flow


class CMIMPORT_23(CmImport23Flow):
    """
    Use case ID:        CMImport_23
    Slogan:             Small Standard Delete Create using Live Config
    """

    NAME = "CMIMPORT_23"

    def run(self):
        self.execute_flow()


cmimport_23 = CMIMPORT_23()
