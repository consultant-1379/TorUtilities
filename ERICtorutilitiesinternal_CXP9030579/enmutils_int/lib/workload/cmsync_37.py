from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSyncProfile


class CMSYNC_37(CMSyncProfile):
    """
    Use Case id:        CMSync_37
    Slogan:             Fronthaul 6020 Sync
    """

    NAME = "CMSYNC_37"

    def run(self):

        self.execute_flow()


cmsync_37 = CMSYNC_37()
