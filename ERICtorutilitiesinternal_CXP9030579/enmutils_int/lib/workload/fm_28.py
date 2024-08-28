from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class FM_28(PlaceHolderFlow):
    """
    KTT profile added for workload diff function only
    """

    NAME = "FM_28"

    def run(self):
        self.execute_flow()


fm_28 = FM_28()
