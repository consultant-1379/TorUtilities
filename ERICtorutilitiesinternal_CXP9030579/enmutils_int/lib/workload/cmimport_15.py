from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_15_flow import CmImport15Flow


class CMIMPORT_15(CmImport15Flow):
    """
    Use Case ID:    CMImport_14
    Slogan:         Get Import Jobs using Preview NBI
    """

    NAME = "CMIMPORT_15"

    def run(self):
        self.execute_flow()


cmimport_15 = CMIMPORT_15()
