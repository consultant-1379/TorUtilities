from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_26(CmExportFlow):
    """
    Use Case id:        CMExport_26
    Slogan:             Full Export for 1 8k BSC Node with all NP attributes
    """

    NAME = "CMEXPORT_26"

    def run(self):
        self.execute_flow()


cmexport_26 = CMEXPORT_26()
