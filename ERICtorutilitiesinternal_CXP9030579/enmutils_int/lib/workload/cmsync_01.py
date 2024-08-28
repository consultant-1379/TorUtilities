from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CmSyncFlow


class CMSYNC_01(CmSyncFlow):
    """
    Use Case id:        CMSync_01
    Slogan:             Rate of create/delete events per second for Average CM Sync notifications
    """

    NAME = "CMSYNC_01"
    SCHEDULE_SLEEP = 1800

    def run(self):

        self.execute_flow()


cmsync_01 = CMSYNC_01()
