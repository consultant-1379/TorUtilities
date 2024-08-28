from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_03(CmImportFlowProfile):
    """
    Use case ID:        CMImport_03
    Slogan:             Large Standard Modify configuration using Non Live Config 2 and Undo
    """

    NAME = "CMIMPORT_03"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_03 = CMIMPORT_03()
