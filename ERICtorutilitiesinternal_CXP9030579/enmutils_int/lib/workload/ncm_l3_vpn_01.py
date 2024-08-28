from enmutils_int.lib.profile_flows.ncm_flows.ncm_l3_vpn_01_flow import NcmL3Vpn01Flow


class NCM_L3_VPN_01(NcmL3Vpn01Flow):
    """
    Use Case ID:    NCM_L3_VPN_01
    Slogan:         Activation & Deactivation of Bulk Commands
    """
    NAME = "NCM_L3_VPN_01"

    def run(self):
        self.execute_flow()


ncm_l3_vpn_01 = NCM_L3_VPN_01()
