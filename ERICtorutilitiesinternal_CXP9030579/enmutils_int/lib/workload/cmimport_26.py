from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_26(CmImportFlowProfile):
    """
    Use Case ID:    CMIMPORT_26
    Slogan:         Large Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_26"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_26 = CMIMPORT_26()
