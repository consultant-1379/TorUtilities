from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_28(CMSyncProfile):
    """
    Use Case id:        CMSync_28
    Slogan:             Router6274 Sync
    """

    NAME = "CMSYNC_28"

    def run(self):
        self.execute_flow()


cmsync_28 = CMSYNC_28()
