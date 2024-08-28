from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow import CmExport19Flow


class CMEXPORT_19(CmExport19Flow):
    """
    Use Case ID:    CMExport_19
    Slogan:         ENIQ Historical Export
    """

    NAME = "CMEXPORT_19"

    def run(self):
        self.execute_flow()


cmexport_19 = CMEXPORT_19()
