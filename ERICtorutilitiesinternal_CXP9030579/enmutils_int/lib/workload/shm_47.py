from enmutils_int.lib.profile_flows.shm_flows.shm_restart_flow import ShmRestartFlow


class SHM_47(ShmRestartFlow):
    """
    Use Case id:        SHM_47
    Slogan:             SHM Baseband Radio node restart
    """
    NAME = "SHM_47"

    def run(self):
        self.execute_flow()


shm_47 = SHM_47()
