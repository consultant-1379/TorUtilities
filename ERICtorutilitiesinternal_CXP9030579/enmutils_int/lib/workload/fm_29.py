from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class FM_29(PlaceHolderFlow):
    """
    KTT profile added for workload diff function only
    """

    NAME = "FM_29"

    def run(self):
        self.execute_flow()


fm_29 = FM_29()
