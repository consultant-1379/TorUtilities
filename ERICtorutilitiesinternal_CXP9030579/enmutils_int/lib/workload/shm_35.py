from enmutils_int.lib.profile_flows.shm_flows.shm_35_flow import Shm35Flow


class SHM_35(Shm35Flow):
    """
    Use Case id:        SHM_35
    Slogan:             SHM CV Cleanup Job
    """
    NAME = "SHM_35"

    def run(self):
        self.execute_flow()


shm_35 = SHM_35()
