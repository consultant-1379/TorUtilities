from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_31(CmImportFlowProfile):
    """
    Use Case id:    CMImport_31
    Slogan:         Small Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_31"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_31 = CMIMPORT_31()
