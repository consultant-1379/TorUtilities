from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync24Flow


class CMSYNC_24(CMSync24Flow):
    """
    Use Case id:        CMSync_24
    Slogan:             Treat-As Sync for Baseband Radio Node
    """
    NAME = "CMSYNC_24"

    def run(self):
        self.execute_flow()


cmsync_24 = CMSYNC_24()
