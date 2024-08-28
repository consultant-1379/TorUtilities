from enmutils_int.lib.profile_flows.shm_flows.shm_06_flow import Shm06Flow


class SHM_06(Shm06Flow):
    """
    Use Case id:        SHM_06
    Slogan:             SHM Active Users
    """
    NAME = "SHM_06"

    def run(self):
        self.execute_flow()


shm_06 = SHM_06()
