from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_27(CmExportFlow):
    """
    Use Case id:        CMExport_27
    Slogan:             Filtered Export of YANG Nodes.
    """

    NAME = "CMEXPORT_27"

    def run(self):
        self.execute_flow()


cmexport_27 = CMEXPORT_27()
