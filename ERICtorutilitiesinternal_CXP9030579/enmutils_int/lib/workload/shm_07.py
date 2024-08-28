from enmutils_int.lib.profile_flows.shm_flows.shm_07_flow import Shm07Flow


class SHM_07(Shm07Flow):
    """
    Use Case id:        SHM_07
    Slogan:             SHM Passive Users
    """
    NAME = "SHM_07"

    def run(self):
        self.execute_flow()


shm_07 = SHM_07()
