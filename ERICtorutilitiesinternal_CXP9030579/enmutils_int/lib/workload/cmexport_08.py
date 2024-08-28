from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_08_flow import CmExport08


class CMEXPORT_08(CmExport08):
    """
    Use Case ID:        CMExport_08
    Slogan:             Export all information for a 3 cell node. Do 10 of these in parallel
    """
    NAME = "CMEXPORT_08"

    def run(self):
        self.execute_flow()


cmexport_08 = CMEXPORT_08()
