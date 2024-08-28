from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_11_flow import CmExport11


class CMEXPORT_11(CmExport11):
    """
    Use Case ID:        CMEXPORT_11
    Slogan:             User defined filtered export for 5 sets of 30 nodes containing 25000 MOs every 6 seconds
                        for a duration of 15 mins
    """

    NAME = "CMEXPORT_11"

    def run(self):
        self.execute_flow()


cmexport_11 = CMEXPORT_11()
