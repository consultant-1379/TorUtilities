from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class CMSYNC_27(PlaceHolderFlow):
    """
    KTT profile added for workload diff function only
    """

    NAME = "CMSYNC_27"

    def run(self):
        self.execute_flow()


cmsync_27 = CMSYNC_27()
