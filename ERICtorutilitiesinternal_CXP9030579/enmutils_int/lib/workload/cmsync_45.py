from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync32Flow


class CMSYNC_45(CMSync32Flow):
    """
    Use Case id:        CMSYNC_45
    Slogan:             Rate of AVC events per Day for cRAN nodes
    """

    NAME = "CMSYNC_45"

    def run(self):

        self.execute_flow()


cmsync_45 = CMSYNC_45()
