from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import ShmSingleUpgradeFlow


class SHM_27(ShmSingleUpgradeFlow):
    """
    Use Case id:        SHM_27
    Slogan:             SHM SIU02/TCU02 Install, Verify, Upgrade, Confirm
    """

    NAME = "SHM_27"

    def run(self):
        self.execute_flow()


shm_27 = SHM_27()
