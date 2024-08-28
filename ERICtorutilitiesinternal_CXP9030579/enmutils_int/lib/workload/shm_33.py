from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import ShmUpdateSoftwarePkgNameFlow


class SHM_33(ShmUpdateSoftwarePkgNameFlow):
    """
    Use Case id:        SHM_33
    Slogan:             Router6672 Upgrade and Confirm. Install and Verify
    """
    NAME = "SHM_33"

    def run(self):
        self.execute_flow()


shm_33 = SHM_33()
