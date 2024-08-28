from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_02_flow import NcmMef02Flow


class NCM_MEF_02(NcmMef02Flow):
    """
    Use Case ID:    NCM_MEF_02
    Slogan:         NCM Node Re-Alignment
    """
    NAME = "NCM_MEF_02"

    def run(self):
        self.execute_flow()


ncm_mef_02 = NCM_MEF_02()
