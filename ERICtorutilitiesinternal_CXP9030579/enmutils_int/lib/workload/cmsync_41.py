from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync32Flow


class CMSYNC_41(CMSync32Flow):
    """
    Use Case id:        CMSync_41
    Slogan:             Rate of AVC events per Day for EPG-OI nodes
    """

    NAME = "CMSYNC_41"

    def run(self):

        self.execute_flow()


cmsync_41 = CMSYNC_41()
