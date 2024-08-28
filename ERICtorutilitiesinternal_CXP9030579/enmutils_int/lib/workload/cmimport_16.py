from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_16(CmImportFlowProfile):
    """
    Use Case ID:    CMImport_16
    Slogan:         Large Dynamic Modify configuration using Live Config
    """

    NAME = "CMIMPORT_16"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_16 = CMIMPORT_16()
