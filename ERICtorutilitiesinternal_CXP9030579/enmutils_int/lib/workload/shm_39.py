from enmutils_int.lib.profile_flows.shm_flows.shm_39_flow import Shm39Flow


class SHM_39(Shm39Flow):
    """
    Use Case id:        SHM_39
    Slogan:             SHM BSC Node Backup
    """

    NAME = "SHM_39"

    def run(self):
        self.execute_flow()


shm_39 = SHM_39()
