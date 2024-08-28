from enmutils_int.lib.profile_flows.shm_flows.shm_backup_flow import Shm02Flow


class SHM_46(Shm02Flow):
    """
    Use Case id:        SHM_46
    Slogan:             SHM RadioNode Backup(Robustness Profile)
    """
    NAME = "SHM_46"

    def run(self):
        self.execute_flow()


shm_46 = SHM_46()
