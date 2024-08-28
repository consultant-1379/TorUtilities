from enmutils_int.lib.profile_flows.esm_nbi_flows.esm_nbi_profile import EsmNbiProfile


class ESM_NBI_01(EsmNbiProfile):
    """
    Use Case ID:    ESM_NBI_01
    Slogan:    ESM NBI profile for cENM to push event files from eric-PM-server to external Interface.
    """
    NAME = "ESM_NBI_01"

    def run(self):
        self.execute_flow()


esm_nbi_01 = ESM_NBI_01()
