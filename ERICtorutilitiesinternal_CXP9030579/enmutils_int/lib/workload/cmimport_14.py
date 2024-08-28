from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_14(CmImportFlowProfile):
    """
    Use Case ID:    CMImport_14
    Slogan:         Small standard Delete/Create configuration using Live Config
    """
    NAME = "CMIMPORT_14"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_14 = CMIMPORT_14()
