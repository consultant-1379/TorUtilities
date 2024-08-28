from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_26(CMSyncProfile):
    """
    Use Case id:        CMSync_26
    Slogan:             Mini-Link Outdoor Sync
    """

    NAME = "CMSYNC_26"

    def run(self):
        self.execute_flow()


cmsync_26 = CMSYNC_26()
