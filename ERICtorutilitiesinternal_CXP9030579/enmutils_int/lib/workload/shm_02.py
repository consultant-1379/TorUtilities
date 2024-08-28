from enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow import Shm02Flow


class SHM_02(Shm02Flow):
    """
    Use Case id:        SHM_02
    Slogan:             SHM RadioNode Backup
    """
    NAME = "SHM_02"

    def run(self):
        self.execute_flow()


shm_02 = SHM_02()
