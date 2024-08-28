from enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow import ShmRestartFlow


class SHM_28(ShmRestartFlow):
    """
    Use Case id:        SHM_28
    Slogan:             SHM DU Radio node restart
    """
    NAME = "SHM_28"

    def run(self):
        self.execute_flow()


shm_28 = SHM_28()
