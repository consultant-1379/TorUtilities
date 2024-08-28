from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_13_flow import CmImport13Flow


class CMIMPORT_13(CmImport13Flow):
    """
    Use Case ID:    CMImport_13
    Slogan:         Small standard modify configuration using Live Config
    """
    NAME = "CMIMPORT_13"

    def run(self):
        self.execute_flow()


cmimport_13 = CMIMPORT_13()
