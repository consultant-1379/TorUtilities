from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CMSync40Flow


class CMSYNC_40(CMSync40Flow):
    """
    Use Case id:        CMSync_40
    Slogan:             CCDM Sync
    """

    NAME = "CMSYNC_40"

    def run(self):

        self.execute_flow()


cmsync_40 = CMSYNC_40()
