from enmutils_int.lib.profile_flows.shm_flows.shm_single_upgrade_flow import Shm24Flow


class SHM_24(Shm24Flow):
    """
    Use Case id:        SHM MINI-LINK Install, Verify, Upgrade, Confirm
    Slogan:             SHM MINI-LINK Install, Verify, Upgrade, Confirm
    """

    NAME = "SHM_24"

    def run(self):

        self.execute_flow()


shm_24 = SHM_24()
