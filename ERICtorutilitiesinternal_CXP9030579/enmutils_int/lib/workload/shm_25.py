from enmutils_int.lib.profile_flows.shm_flows.shm_25_flow import Shm25Flow


class SHM_25(Shm25Flow):
    """
    Use Case id:        SHM_25
    Slogan:             SHM upgrade Robustness, node delayed restart
    """
    NAME = "SHM_25"

    def run(self):
        self.execute_flow()


shm_25 = SHM_25()
