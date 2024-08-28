from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class ENMCLI_04(PlaceHolderFlow):
    """
    Use case id:    CMCLI_04 ST_STKPI_CMCHANGE_01
    Slogan:         CMCLI SET data for all LTE network elements
    """

    NAME = "ENMCLI_04"

    def run(self):
        self.execute_flow()


enmcli_04 = ENMCLI_04()
