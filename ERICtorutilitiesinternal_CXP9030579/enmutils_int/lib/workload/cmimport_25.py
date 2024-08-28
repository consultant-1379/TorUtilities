from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_25(CmImportFlowProfile):
    """
    Use Case ID:    CMIMPORT_25
    Slogan:         Large Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_25"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_25 = CMIMPORT_25()
