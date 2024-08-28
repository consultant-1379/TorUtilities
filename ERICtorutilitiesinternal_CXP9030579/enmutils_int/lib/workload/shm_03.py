from enmutils_int.lib.profile_flows.shm_flows.shm_03_flow import Shm03Flow


class SHM_03(Shm03Flow):
    """
    Use Case id:        SHM_03 ST_STKPI_SHM_03
    Slogan:             SHM DU Radio Install, Verify, Upgrade, Confirm
    """
    NAME = "SHM_03"

    def run(self):
        self.execute_flow()


shm_03 = SHM_03()
