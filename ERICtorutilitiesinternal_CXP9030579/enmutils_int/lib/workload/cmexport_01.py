from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_01(CmExportFlow):
    """
    Use Case ID:        CMEXPORT_01 (ST_STKPI_CM_Export_01)
    Slogan:             Two Full RAN Network Export (for the CM Planning Tool)
    """
    NAME = "CMEXPORT_01"

    def run(self):
        self.execute_flow()


cmexport_01 = CMEXPORT_01()
