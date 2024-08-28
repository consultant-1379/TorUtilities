from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_13(CmExportFlow):
    """
    Use Case id:        CMExport_13
    Slogan:             CORE Network Export
    """

    NAME = "CMEXPORT_13"

    def run(self):
        self.execute_flow()


cmexport_13 = CMEXPORT_13()
