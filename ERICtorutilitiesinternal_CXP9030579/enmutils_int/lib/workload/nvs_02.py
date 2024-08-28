from enmutils_int.lib.profile_flows.nvs_flows.nvs_flows import Nvs02Flow


class NVS_02(Nvs02Flow):
    """
    Use Case ID:    NVS_02
    Slogan:         New Node version model removal
    """
    NAME = "NVS_02"

    def run(self):
        self.execute_flow()


nvs_02 = NVS_02()
