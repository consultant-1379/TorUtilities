from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_29(CMSyncProfile):
    """
    Use Case id:        CMSync_29
    Slogan:             BSC Sync
    """

    NAME = "CMSYNC_29"

    def run(self):
        self.execute_flow()


cmsync_29 = CMSYNC_29()
