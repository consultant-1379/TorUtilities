from enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow import Shm18Flow


class SHM_18(Shm18Flow):
    """
    Use Case id:        SHM_18
    Slogan:             SHM Rollback and Restore
    """
    NAME = "SHM_18"

    def run(self):
        self.execute_flow()


shm_18 = SHM_18()
