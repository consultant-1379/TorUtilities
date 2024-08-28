from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_17(CmImportFlowProfile):
    """
    Use Case ID:    CMImport_17
    Slogan:         Large Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_17"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_17 = CMIMPORT_17()
