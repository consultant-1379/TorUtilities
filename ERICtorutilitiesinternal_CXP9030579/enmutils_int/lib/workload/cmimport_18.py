from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_18(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_18
    Slogan:             Small standard Delete Create configuration using Live config
    """

    NAME = "CMIMPORT_18"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_18 = CMIMPORT_18()
