
from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_20(CmImportFlowProfile):
    """
    Use Case id:    CMImport_20
    Slogan:         Large Standard Modify configuration using Live Config
    """

    NAME = "CMIMPORT_20"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_20 = CMIMPORT_20()
