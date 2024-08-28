from enmutils_int.lib.profile_flows.shm_flows.shm_41_flow import Shm41Flow


class SHM_41(Shm41Flow):
    """
    Use Case id:        SHM_41
    Slogan:             SHM Router6675 Node Backup
    """
    NAME = "SHM_41"

    def run(self):
        self.execute_flow()


shm_41 = SHM_41()
