from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_32(CmImportFlowProfile):
    """
    Use Case id:    CMImport_32
    Slogan:         Small Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_32"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_32 = CMIMPORT_32()
