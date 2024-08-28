from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_33(CmImportFlowProfile):
    """
    Use case ID:        CMImport_33
    Slogan:             Small Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_33"
    SCHEDULED_TIMES = []

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_33 = CMIMPORT_33()
