from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_38(CMSyncProfile):
    """
    Use Case id:        CMSync_38
    Slogan:             Juniper Sync
    """

    NAME = "CMSYNC_38"

    def run(self):
        self.execute_flow()


cmsync_38 = CMSYNC_38()
