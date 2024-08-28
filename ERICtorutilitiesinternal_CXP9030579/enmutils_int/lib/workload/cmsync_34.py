from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync34Flow


class CMSYNC_34(CMSync34Flow):
    """
    Use Case id:        CMSync_34
    Slogan:             Fully Syncing 1k Mini-Link Indoor Nodes
    """

    NAME = "CMSYNC_34"

    def run(self):

        self.execute_flow()


cmsync_34 = CMSYNC_34()
