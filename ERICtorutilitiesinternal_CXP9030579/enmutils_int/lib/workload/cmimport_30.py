from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_30(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_30
    Slogan:             Large Standard Modify configuration using Live Config
    """

    NAME = 'CMIMPORT_30'

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_30 = CMIMPORT_30()
