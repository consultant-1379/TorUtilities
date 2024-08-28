from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CmSyncFlow


class CMSYNC_04(CmSyncFlow):
    """
    Use Case id:        CMSync_04
    Slogan:             Rate of AVC events per second for Peak CM Sync notifications
    """
    NAME = "CMSYNC_04"

    def run(self):
        self.execute_flow()


cmsync_04 = CMSYNC_04()
