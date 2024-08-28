from enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow import Shm01Flow


class SHM_01(Shm01Flow):
    """
    Use Case id:        SHM_01 ST_STKPI_SHM_02
    Slogan:             SHM DU Radio Backup
    """
    NAME = "SHM_01"

    def run(self):
        self.execute_flow()


shm_01 = SHM_01()
