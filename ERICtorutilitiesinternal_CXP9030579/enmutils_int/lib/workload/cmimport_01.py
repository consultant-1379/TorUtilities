from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_01(CmImportFlowProfile):
    """
    Use case ID:        CMImport_01
    Slogan:             Small Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_01"
    SCHEDULED_TIMES = []

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_01 = CMIMPORT_01()
