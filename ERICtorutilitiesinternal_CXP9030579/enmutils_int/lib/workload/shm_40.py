from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import ShmUpdateSoftwarePkgNameFlow


class SHM_40(ShmUpdateSoftwarePkgNameFlow):
    """
    Use Case id:        SHM_40
    Slogan:             SHM Router6675 Install, Verify, Upgrade, Confirm
    """
    NAME = "SHM_40"

    def run(self):
        self.execute_flow()


shm_40 = SHM_40()
