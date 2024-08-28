from enmutils_int.lib.profile_flows.shm_flows.shm_export_flow import Shm20Flow


class SHM_20(Shm20Flow):
    """

    Use Case id:        SHM_20
    Slogan:             Software Export
    """

    NAME = "SHM_20"

    def run(self):
        self.execute_flow()


shm_20 = SHM_20()
