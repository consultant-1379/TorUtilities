from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_04(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_04
    Slogan:             Large Dynamic Delete/Create configuration using Live Config
    """

    NAME = "CMIMPORT_04"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_04 = CMIMPORT_04()
