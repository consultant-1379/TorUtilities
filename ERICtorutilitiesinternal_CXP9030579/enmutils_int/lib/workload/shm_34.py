from enmutils_int.lib.profile_flows.shm_flows.shm_34_flow import Shm34Flow


class SHM_34(Shm34Flow):
    """
    Use Case id:        SHM_34
    Slogan:             SHM Router6672 Node Backup
    """
    NAME = "SHM_34"

    def run(self):
        self.execute_flow()


shm_34 = SHM_34()
