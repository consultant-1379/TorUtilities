from enmutils_int.lib.profile_flows.shm_flows.shm_23_flow import Shm23Flow


class SHM_23(Shm23Flow):
    """
    Use Case id:        SHM_23
    Slogan:             SHM MINI-LINK Backup
    """
    NAME = "SHM_23"

    def run(self):
        self.execute_flow()


shm_23 = SHM_23()
