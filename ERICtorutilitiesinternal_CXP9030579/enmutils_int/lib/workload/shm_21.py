from enmutils_int.lib.profile_flows.shm_flows.shm_export_flow import Shm21Flow


class SHM_21(Shm21Flow):
    """

    Use Case id:        SHM_21
    Slogan:             Licence Export
    """

    NAME = "SHM_21"

    def run(self):
        self.execute_flow()


shm_21 = SHM_21()
