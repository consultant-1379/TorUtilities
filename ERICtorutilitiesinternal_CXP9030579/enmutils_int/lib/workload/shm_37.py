from enmutils_int.lib.profile_flows.shm_flows.shm_37_flow import Shm37Flow


class SHM_37(Shm37Flow):
    """
    Use Case id:        SHM_37
    Slogan:             SHM Delete upgrade packages via REST Call
    """
    NAME = "SHM_37"

    def run(self):
        self.execute_flow()


shm_37 = SHM_37()
