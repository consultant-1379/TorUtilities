from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_20(CMSyncProfile):
    """
    Use Case id:        CMSync_20
    Slogan:             RNC Sync
    """

    NAME = "CMSYNC_20"

    def run(self):
        self.execute_flow()


cmsync_20 = CMSYNC_20()
