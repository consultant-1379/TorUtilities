from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import SimplifiedParallelCmImportFlow


class CMIMPORT_22(SimplifiedParallelCmImportFlow):
    """
    Use Case ID:    CMImport_22
    Slogan:         Large standard Delete Create configuration using Live config
    """
    NAME = "CMIMPORT_22"

    def run(self):
        self.execute_flow()


cmimport_22 = CMIMPORT_22()
