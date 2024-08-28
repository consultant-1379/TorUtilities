from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CmSyncFlow


class CMSYNC_06(CmSyncFlow):
    """
    Use Case id:        CMSync_06
    Slogan:             Rate of AVC events per second for Storm CM Sync notifications
    """
    NAME = "CMSYNC_06"

    def run(self):
        self.execute_flow()


cmsync_06 = CMSYNC_06()
