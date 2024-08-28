from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class FM_23(PlaceHolderFlow):
    """
    Use case id:    FM_23 ST_STKPI_FM_01
    Slogan:         Alarm visible in GUI
    """

    NAME = "FM_23"

    def run(self):
        self.execute_flow()


fm_23 = FM_23()
