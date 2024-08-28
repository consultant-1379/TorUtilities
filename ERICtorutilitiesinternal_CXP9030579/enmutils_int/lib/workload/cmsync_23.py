from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync23Flow


class CMSYNC_23(CMSync23Flow):
    """
    Use Case id:        CMSync_23
    Slogan:             Mega storm CM Sync notifications
    """

    NAME = "CMSYNC_23"

    def run(self):
        self.execute_flow()


cmsync_23 = CMSYNC_23()
