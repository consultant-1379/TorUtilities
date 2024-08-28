from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_12(CmExportFlow):
    """
    Use Case ID:        CMExport_12
    Slogan:             1 Full RAN and CORE Network Export (for the CM Planning Tool)
    """

    NAME = "CMEXPORT_12"

    def run(self):
        self.execute_flow()


cmexport_12 = CMEXPORT_12()
