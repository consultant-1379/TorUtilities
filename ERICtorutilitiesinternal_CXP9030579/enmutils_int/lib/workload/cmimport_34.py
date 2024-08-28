from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import CmImportFlowProfile


class CMIMPORT_34(CmImportFlowProfile):
    """
    Use Case id:        CMIMPORT_34
    Slogan:             Yang CmImport Create/Delete
    """

    NAME = "CMIMPORT_34"

    def run(self):
        self.execute_cmimport_common_flow()


cmimport_34 = CMIMPORT_34()
