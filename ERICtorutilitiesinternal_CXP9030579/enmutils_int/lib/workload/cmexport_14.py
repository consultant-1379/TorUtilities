from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_14(CmExportFlow):
    """
    Use Case id:        CMExport_14
    Slogan:             IP Transport Network Export
    """

    NAME = "CMEXPORT_14"

    def run(self):
        self.execute_flow()


cmexport_14 = CMEXPORT_14()
