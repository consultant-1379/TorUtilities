from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_01_flow import NcmMef01Flow


class NCM_MEF_01(NcmMef01Flow):
    """
    Use Case ID:    NCM_MEF_01
    Slogan:         NCM Node & Link Re-Alignment
    """
    NAME = "NCM_MEF_01"

    def run(self):
        self.execute_flow()


ncm_mef_01 = NCM_MEF_01()
