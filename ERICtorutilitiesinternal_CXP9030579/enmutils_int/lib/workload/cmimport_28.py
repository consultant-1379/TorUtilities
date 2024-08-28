from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_28(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_28
    Slogan:             Large Standard Modify configuration using Live Config
    """

    NAME = 'CMIMPORT_28'

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_28 = CMIMPORT_28()
