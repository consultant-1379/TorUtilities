from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync32Flow


class CMSYNC_44(CMSync32Flow):
    """
    Use Case id:        CMSync_44
    Slogan:             Rate of AVC events per Day for PCG nodes
    """

    NAME = "CMSYNC_44"

    def run(self):

        self.execute_flow()


cmsync_44 = CMSYNC_44()
