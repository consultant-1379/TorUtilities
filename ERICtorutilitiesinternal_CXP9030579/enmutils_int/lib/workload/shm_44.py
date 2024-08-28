from enmutils_int.lib.profile_flows.shm_flows.shm_44_flow import Shm44Flow


class SHM_44(Shm44Flow):
    """
    Use Case id:        SHM_44
    Slogan:             SHM SCU Upgrade
    """
    NAME = "SHM_44"

    def run(self):
        self.execute_flow()


shm_44 = SHM_44()
