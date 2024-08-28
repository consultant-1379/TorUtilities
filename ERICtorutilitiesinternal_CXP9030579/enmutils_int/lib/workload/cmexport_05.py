from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_05(CmExportFlow):
    """
    Use Case ID:        CMEXPORT_05
    Slogan:             SON Daily Topology only Export using SON user defined filter
    """

    NAME = "CMEXPORT_05"

    def run(self):
        self.execute_flow()


cmexport_05 = CMEXPORT_05()
