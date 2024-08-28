from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_29(CmImportFlowProfile):
    """
    Use case ID:        CMImport_29
    Slogan:             Large Standard Modify Config using Live Config
    """

    NAME = "CMIMPORT_29"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_29 = CMIMPORT_29()
