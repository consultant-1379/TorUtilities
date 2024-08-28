from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_42(CMSyncProfile):
    """
    Use Case id:        CMSync_42
    Slogan:             Single Node PCG Node Sync
    """

    NAME = "CMSYNC_42"

    def run(self):

        self.execute_flow()


cmsync_42 = CMSYNC_42()
