from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_19(CmImportFlowProfile):
    """
    Use Case ID:    CMImport_19
    Slogan:         Large standard Delete Create configuration using Live config
    """

    NAME = "CMIMPORT_19"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_19 = CMIMPORT_19()
