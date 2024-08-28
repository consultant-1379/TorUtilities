from enmutils_int.lib.profile_flows.shm_flows.shm_export_flow import Shm19Flow


class SHM_19(Shm19Flow):
    """

    Use Case id:        SHM_19
    Slogan:             Hardware Export
    """

    NAME = "SHM_19"

    def run(self):
        self.execute_flow()


shm_19 = SHM_19()
