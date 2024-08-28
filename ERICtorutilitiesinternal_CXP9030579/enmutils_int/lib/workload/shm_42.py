from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import Shm42Flow


class SHM_42(Shm42Flow):
    """
    Use Case id:        SHM MINI-LINK-6691 Install, Verify, Upgrade, Confirm
    Slogan:             SHM MINI-LINK-6691 Install, Verify, Upgrade, Confirm
    """

    NAME = "SHM_42"

    def run(self):

        self.execute_flow()


shm_42 = SHM_42()
