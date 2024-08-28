from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class PM_35(PlaceHolderFlow):
    """
    Use Case ID:    PM_35 ST_STKPI_PM_01
    Slogan:         File collection (Pull)
    """

    NAME = "PM_35"

    def run(self):
        self.execute_flow()


pm_35 = PM_35()
