from enmutils_int.lib.profile_flows.shm_flows.shm_45_flow import Shm45Flow


class SHM_45(Shm45Flow):
    """
    Use Case id:        SHM_45
    Slogan:             SHM Backup flow for DSC, FRONTHAUL-6020, MGW, MTAS, SGSN-MME, PCG
    """
    NAME = "SHM_45"

    def run(self):
        self.execute_flow()


shm_45 = SHM_45()
