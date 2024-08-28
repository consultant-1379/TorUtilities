from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_23_flow import CmExport23Flow


class CMEXPORT_23(CmExport23Flow):

    """
    Use Case id:        CMExport_23
    Slogan:             Filtered Export of Inventory Information.
    """

    NAME = "CMEXPORT_23"

    def run(self):
        self.execute_flow()


cmexport_23 = CMEXPORT_23()
