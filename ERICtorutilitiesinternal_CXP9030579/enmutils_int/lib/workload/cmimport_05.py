from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_05(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_05
    Slogan:             Large Standard Modify configuration using Live Config
    """

    NAME = 'CMIMPORT_05'

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_05 = CMIMPORT_05()
