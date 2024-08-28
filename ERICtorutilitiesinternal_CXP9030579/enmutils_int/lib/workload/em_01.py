from enmutils_int.lib.profile_flows.em_flows.em_01_flow import EM01Flow


class EM_01(EM01Flow):
    """
    Use Case ID:        EM_01
    Slogan:             Element Manager
    """
    NAME = "EM_01"

    def run(self):
        self.execute_flow()


em_01 = EM_01()
