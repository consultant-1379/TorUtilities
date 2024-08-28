from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_22(CmExportFlow):
    """
    Use Case id:        CMExport_22
    Slogan:             Filtered Export with Non Persistent Attributes for all BSCs.
    """

    NAME = "CMEXPORT_22"

    def run(self):
        self.execute_flow()


cmexport_22 = CMEXPORT_22()
