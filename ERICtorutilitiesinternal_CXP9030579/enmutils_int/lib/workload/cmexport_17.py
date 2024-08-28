from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_17_flow import CmExport17


class CMEXPORT_17(CmExport17):
    """
    Use Case ID:        CMExport_17
    Slogan:             Download Exports
    """

    NAME = "CMEXPORT_17"

    def run(self):
        self.execute_flow()


cmexport_17 = CMEXPORT_17()
