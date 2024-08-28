from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_19(CMSyncProfile):
    """
    Use Case id:        CMSync_19
    Slogan:             RBS Sync
    """

    NAME = "CMSYNC_19"

    def run(self):
        self.execute_flow()


cmsync_19 = CMSYNC_19()
