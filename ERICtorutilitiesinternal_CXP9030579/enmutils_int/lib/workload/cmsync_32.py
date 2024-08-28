from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync32Flow


class CMSYNC_32(CMSync32Flow):
    """
    Use Case id:        CMSync_32
    Slogan:             Rate of AVC events per second for Average CM notifications for GSM through the BSC
    """

    NAME = "CMSYNC_32"

    def run(self):
        self.execute_flow()


cmsync_32 = CMSYNC_32()
