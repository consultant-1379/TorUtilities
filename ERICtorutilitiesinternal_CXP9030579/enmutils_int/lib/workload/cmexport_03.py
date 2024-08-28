from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow


class CMEXPORT_03(CmExportFlow):
    """
    Use Case ID:        CMExport_03
    Slogan:             20 RAN Exports in Parallel (of various sizes)
    """
    NAME = "CMEXPORT_03"

    def run(self):
        self.execute_parallel_flow()


cmexport_03 = CMEXPORT_03()
