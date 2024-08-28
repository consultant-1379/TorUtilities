from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_07(CmExportFlow):
    """
    Use Case id:        CMExport_07
    Slogan:             Export Batch of Nodes to Simulate Customer Subnetwork export.
    """
    NAME = "CMEXPORT_07"

    def run(self):
        self.execute_flow()


cmexport_07 = CMEXPORT_07()
