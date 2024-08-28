from enmutils_int.lib.profile_flows.shm_flows.shm_32_flow import Shm32Flow


class SHM_32(Shm32Flow):
    """
    Use Case id:        SHM_32
    Slogan:             SHM Mini-Link Outdoor Node Backup
    """
    NAME = "SHM_32"

    def run(self):
        self.execute_flow()


shm_32 = SHM_32()
