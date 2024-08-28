from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync39Flow


class CMSYNC_39(CMSync39Flow):
    """
    Use Case id:        CMSync_39
    Slogan:             EPG-OI Sync
    """

    NAME = "CMSYNC_39"

    def run(self):

        self.execute_flow()


cmsync_39 = CMSYNC_39()
