from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_02_flow import CmExport02


class CMEXPORT_02(CmExport02):
    """
    Use Case ID:        CMExport_02
    Slogan:             Up to 3 Large Exports are performed concurrently,
                        of which a maximum of 2 can be entire network exports.
    """

    NAME = "CMEXPORT_02"

    def run(self):
        self.execute_flow()


cmexport_02 = CMEXPORT_02()
