from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_21(CmImportFlowProfile):
    """
    Use Case ID:    CMImport_21
    Slogan:         Small Standard Modify configuration using Live Config
    """
    NAME = "CMIMPORT_21"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_21 = CMIMPORT_21()
