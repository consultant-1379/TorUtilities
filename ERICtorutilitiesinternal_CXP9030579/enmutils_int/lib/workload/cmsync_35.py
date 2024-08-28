from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync35Flow


class CMSYNC_35(CMSync35Flow):
    """
    Use Case id:        CMSync_35
    Slogan:             BSC Sync
    """

    NAME = "CMSYNC_35"

    def run(self):

        self.execute_flow()


cmsync_35 = CMSYNC_35()
