from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class BUR_02(PlaceHolderFlow):

    """
    Use Case id:        BUR_02 ST_STKPI_BUR_02
    Slogan:             Restore the ENM Deployment
    """

    NAME = "BUR_02"

    def run(self):
        self.execute_flow()


bur_02 = BUR_02()
