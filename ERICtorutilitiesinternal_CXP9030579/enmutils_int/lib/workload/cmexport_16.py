from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow import CmExport16


class CMEXPORT_16(CmExport16):
    """
    Use Case id:        CMExport_16
    Slogan:             SHM inventory export
    """

    NAME = "CMEXPORT_16"

    def run(self):
        self.execute_flow()


cmexport_16 = CMEXPORT_16()
