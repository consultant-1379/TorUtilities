from enmutils_int.lib.profile_flows.cmsync_flows.cmsync_flow import CmSyncSetupFlow


class CMSYNC_SETUP(CmSyncSetupFlow):
    """
    Pre-requisite to running CMSYNC 1 - 6
    """

    NAME = "CMSYNC_SETUP"

    def run(self):
        self.execute_flow()


cmsync_setup = CMSYNC_SETUP()
