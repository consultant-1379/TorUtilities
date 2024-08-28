from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_03_flow import NcmMef03Flow


class NCM_MEF_03(NcmMef03Flow):
    """
    Use Case ID:    NCM_MEF_03
    Slogan:         NCM Full Re-Alignement
    """

    NAME = "NCM_MEF_03"

    def run(self):
        self.execute_flow()


ncm_mef_03 = NCM_MEF_03()
