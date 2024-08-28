from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_08_flow import CmImport08Flow


class CMIMPORT_08(CmImport08Flow):
    """
    Use Case id:        CMIMPORT_08
    Slogan:             Small Dynamic Modify configuration using Live Config
    """

    NAME = "CMIMPORT_08"

    def run(self):
        self.execute_flow()


cmimport_08 = CMIMPORT_08()
