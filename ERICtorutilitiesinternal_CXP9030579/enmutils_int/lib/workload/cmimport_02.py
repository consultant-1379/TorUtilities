from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_02(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_02
    Slogan:             Small Dynamic Delete/Create configuration using Live Config
    """

    NAME = "CMIMPORT_02"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_02 = CMIMPORT_02()
