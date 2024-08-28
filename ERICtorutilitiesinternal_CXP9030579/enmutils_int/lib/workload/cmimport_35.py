from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_35(CmImportFlowProfile):
    """
    Use case ID:        CMImport_35
    Slogan:             Small Dynamic Modify configuration using Live Config
    """

    NAME = "CMIMPORT_35"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_35 = CMIMPORT_35()
