from enmutils_int.lib.profile_flows.shm_flows.shm_05_flow import Shm05Flow


class SHM_05(Shm05Flow):
    """
    Use Case id:        SHM_05
    Slogan:             SHM RadioNode Install, Verify, Upgrade, Confirm
    """
    NAME = "SHM_05"

    def run(self):
        self.execute_flow()


shm_05 = SHM_05()
