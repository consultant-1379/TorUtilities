from enmutils_int.lib.profile_flows.shm_flows.shm_43_flow import Shm43Flow


class SHM_43(Shm43Flow):
    """
    Use Case id:        SHM_43
    Slogan:             SHM MINI-LINK-669x Backup
    """
    NAME = "SHM_43"

    def run(self):
        self.execute_flow()


shm_43 = SHM_43()
