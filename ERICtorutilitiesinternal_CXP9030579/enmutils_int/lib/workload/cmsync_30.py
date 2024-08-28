from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync30Flow


class CMSYNC_30(CMSync30Flow):
    """
    Use Case id:        CMSync_30
    Slogan:             Fully Syncing 1000 eNodeB DU Radio Node
    """

    NAME = "CMSYNC_30"

    def run(self):

        self.execute_flow()


cmsync_30 = CMSYNC_30()
