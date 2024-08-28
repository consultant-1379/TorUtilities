from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import ShmUpdateSoftwarePkgNameFlow


class SHM_31(ShmUpdateSoftwarePkgNameFlow):
    """
    Use Case id:        SHM_31
    Slogan:             SHM MINI-LINK Outdoor Install, Verify, Upgrade, Confirm
    """

    NAME = "SHM_31"

    def run(self):
        self.execute_flow()


shm_31 = SHM_31()
