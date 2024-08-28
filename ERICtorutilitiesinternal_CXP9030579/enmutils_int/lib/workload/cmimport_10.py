from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_10(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_10
    Slogan:             Large Dynamic Modify configuration using Live Config
    """

    NAME = 'CMIMPORT_10'

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_10 = CMIMPORT_10()
