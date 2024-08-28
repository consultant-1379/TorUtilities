from enmutils_int.lib.profile_flows.ncm_flows.ncm_vpn_sd_01_flow import NcmVpnSd01Flow


class NCM_VPN_SD_01(NcmVpnSd01Flow):
    """
    Use Case ID:    NCM_VPN_SD_01
    Slogan:         NCM VPN Service Discovery
    """
    NAME = "NCM_VPN_SD_01"

    def run(self):
        self.execute_flow()


ncm_vpn_sd_01 = NCM_VPN_SD_01()
