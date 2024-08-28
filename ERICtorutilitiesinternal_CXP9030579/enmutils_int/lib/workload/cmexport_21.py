from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_21(CmExportFlow):
    """
    Use Case id:        CMExport_21
    Slogan:             Full Export for 1 2k BSC Node
    """

    NAME = "CMEXPORT_21"

    def run(self):
        self.execute_flow()


cmexport_21 = CMEXPORT_21()
