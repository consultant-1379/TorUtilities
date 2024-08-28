from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_24(CmImportFlowProfile):
    """
    Use Case ID:    CMIMPORT_24
    Slogan:         Large Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_24"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_24 = CMIMPORT_24()
