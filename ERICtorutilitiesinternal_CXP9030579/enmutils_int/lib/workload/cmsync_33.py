from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync33Flow


class CMSYNC_33(CMSync33Flow):
    """
    Use Case id:        CMSync_33
    Slogan:             Fully Syncing 1000 Router6000 Nodes
    """

    NAME = "CMSYNC_33"

    def run(self):

        self.execute_flow()


cmsync_33 = CMSYNC_33()
