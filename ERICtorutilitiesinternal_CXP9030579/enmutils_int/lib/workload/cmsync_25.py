from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync25Flow


class CMSYNC_25(CMSync25Flow):
    """
    Use Case id:        CMSync_25
    Slogan:             Fully Syncing 1000 eNodeB Baseband Radio Node
    """

    NAME = "CMSYNC_25"

    def run(self):

        self.execute_flow()


cmsync_25 = CMSYNC_25()
