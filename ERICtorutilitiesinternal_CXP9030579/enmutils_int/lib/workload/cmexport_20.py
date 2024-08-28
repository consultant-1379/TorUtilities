from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_20(CmExportFlow):
    """
    Use Case ID:    CMExport_20
    Slogan:         Dynamic filtered export
    """

    NAME = "CMEXPORT_20"

    def run(self):
        self.execute_flow()


cmexport_20 = CMEXPORT_20()
