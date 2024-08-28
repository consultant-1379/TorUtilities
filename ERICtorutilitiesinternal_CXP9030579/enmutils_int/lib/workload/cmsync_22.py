from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class CMSYNC_22(PlaceHolderFlow):
    """
    Use Case id:        CMSync_22 ST_STKPI_CM_Synch_02
    Slogan:             SGSN-MME Sync
    """
    NAME = "CMSYNC_22"

    def run(self):
        self.execute_flow()


cmsync_22 = CMSYNC_22()
