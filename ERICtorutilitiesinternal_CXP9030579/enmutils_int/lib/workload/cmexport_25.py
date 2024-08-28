from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_25(CmExportFlow):
    """
    Use Case id:        CMExport_25
    Slogan:             Yang Export 80 PCG Nodes and 40 CCDM Nodes
    """

    NAME = "CMEXPORT_25"

    def run(self):
        self.execute_flow()


cmexport_25 = CMEXPORT_25()
