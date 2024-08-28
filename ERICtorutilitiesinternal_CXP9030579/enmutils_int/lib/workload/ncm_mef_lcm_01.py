from enmutils_int.lib.profile_flows.ncm_flows.ncm_mef_lcm_01_flow import NcmMefLcm01Flow


class NCM_MEF_LCM_01(NcmMefLcm01Flow):
    """
    Use Case ID:    NCM_MEF_LCM_01
    Slogan:         Activation & Deactivation of Bulk Commands
    """
    NAME = "NCM_MEF_LCM_01"

    def run(self):
        self.execute_flow()


ncm_mef_lcm_01 = NCM_MEF_LCM_01()
