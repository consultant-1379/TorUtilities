from enmutils_int.lib.profile_flows.esm_flows.esm_flow import ESM01Flow


class ESM_01(ESM01Flow):
    """
    Use Case ID:        ESM_01
    Slogan:             Active users
    """

    NAME = "ESM_01"

    def run(self):
        self.execute_flow()


esm_01 = ESM_01()
