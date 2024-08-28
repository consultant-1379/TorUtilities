from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_18_flow import CmExport18


class CMEXPORT_18(CmExport18):
    """
    Use Case id:        CMExport_18
    Slogan:             EBS Topology Exports
    """

    NAME = "CMEXPORT_18"

    def run(self):
        self.execute_flow()


cmexport_18 = CMEXPORT_18()
