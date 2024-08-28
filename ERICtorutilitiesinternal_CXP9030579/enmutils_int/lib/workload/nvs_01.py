from enmutils_int.lib.profile_flows.nvs_flows.nvs_flows import Nvs01Flow


class NVS_01(Nvs01Flow):
    """
    Use Case ID:    NVS_01
    Slogan:         New Node version model introduction
    """
    NAME = "NVS_01"

    def run(self):
        self.execute_flow()


nvs_01 = NVS_01()
