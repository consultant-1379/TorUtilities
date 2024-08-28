from enmutils_int.lib.profile_flows.shm_flows.shm_04_flow import Shm04Flow


class SHM_04(Shm04Flow):
    """
    Use Case id:        SHM_04 ST_STKPI_SHM_01
    Slogan:             SHM DU Radio Inventory Sync
    """
    NAME = "SHM_04"

    def run(self):
        self.execute_flow()


shm_04 = SHM_04()
