from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_43(CMSyncProfile):
    """
    Use Case id:        CMSync_43
    Slogan:             Full Yang Node Sync
    """

    NAME = "CMSYNC_43"

    def run(self):

        self.execute_flow()


cmsync_43 = CMSYNC_43()
