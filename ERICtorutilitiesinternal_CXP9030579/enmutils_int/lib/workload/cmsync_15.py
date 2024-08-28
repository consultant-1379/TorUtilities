from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync15Flow


class CMSYNC_15(CMSync15Flow):
    """
    Use Case id:        CMSync_15
    Slogan:             Rate of AVC events per second for Transport.
    """

    NAME = "CMSYNC_15"

    def run(self):
        self.execute_flow()


cmsync_15 = CMSYNC_15()
