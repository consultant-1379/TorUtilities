from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class FM_24(PlaceHolderFlow):
    """
    Use case id:    FM_24 ST_STKPI_FM_02
    Slogan:         Alarm reporting to NMS
    """
    NAME = "FM_24"

    def run(self):
        self.execute_flow()


fm_24 = FM_24()
