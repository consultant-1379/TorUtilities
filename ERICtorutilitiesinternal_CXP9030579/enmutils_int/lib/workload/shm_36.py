from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import ShmSingleUpgradeFlow


class SHM_36(ShmSingleUpgradeFlow):
    """
    Use Case id:        SHM_36
    Slogan:             SHM BSC Node Upgrade Install Verify Upgrade Confirm
    """
    NAME = "SHM_36"

    def run(self):
        self.execute_flow()


shm_36 = SHM_36()
