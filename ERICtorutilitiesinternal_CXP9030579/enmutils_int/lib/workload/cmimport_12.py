from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_12(CmImportFlowProfile):
    """
    Use Case ID:    CMImport_12
    Slogan:         Small Dynamic Modify configuration using Live Config
    """

    NAME = "CMIMPORT_12"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_12 = CMIMPORT_12()
