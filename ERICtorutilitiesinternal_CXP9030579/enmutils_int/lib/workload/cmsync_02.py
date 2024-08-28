from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CmSyncFlow


class CMSYNC_02(CmSyncFlow):
    """
    Use Case id:        CMSync_02
    Slogan:             Rate of AVC events per second for Average CM Sync notifications
    """
    NAME = "CMSYNC_02"

    def run(self):
        self.execute_flow()


cmsync_02 = CMSYNC_02()
