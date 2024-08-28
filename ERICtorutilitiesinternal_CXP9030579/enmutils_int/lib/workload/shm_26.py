from enmutils_int.lib.profile_flows.shm_flows.shm_restore_flow import Shm26Flow


class SHM_26(Shm26Flow):
    """
    Use Case id:        SHM_26
    Slogan:             SHM Restore Robustness, node delayed restart
    """
    NAME = "SHM_26"

    def run(self):
        self.execute_flow()


shm_26 = SHM_26()
