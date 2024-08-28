from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class CMSYNC_21(PlaceHolderFlow):
    """
    Use Case id:        CMSync_21 ST_STKPI_CM_Synch_01
    Slogan:             eNodeB DU Radio Sync
    """
    NAME = "CMSYNC_21"

    def run(self):
        self.execute_flow()


cmsync_21 = CMSYNC_21()
