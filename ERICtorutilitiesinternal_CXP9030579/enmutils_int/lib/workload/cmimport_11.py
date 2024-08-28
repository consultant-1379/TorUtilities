from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_11(CmImportFlowProfile):
    """
    Use case ID:        CMImport_11
    Slogan:             Large Standard Modify Config using Live Config
    """

    NAME = "CMIMPORT_11"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_11 = CMIMPORT_11()
