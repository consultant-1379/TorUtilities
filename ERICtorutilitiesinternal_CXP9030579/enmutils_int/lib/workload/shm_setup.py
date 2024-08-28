from enmutils_int.lib.profile_flows.shm_flows.shm_setup_flow import ShmSetupFlow


class SHM_SETUP(ShmSetupFlow):
    """
    Requirement to run before executing SHM_03, SHM_05, SHM_06, SHM_24, SHM_25, SHM_27, SHM_31, SHM_33, SHM_36,
                                        SHM_40, SHM_41, SHM_42, SHM_43, SHM_44, ASU_01

    Use Case id:        SHM_SETUP
    Slogan:             SHM Bandwidth setting and Import files
    """
    NAME = "SHM_SETUP"

    def run(self):
        self.execute_flow()


shm_setup = SHM_SETUP()
