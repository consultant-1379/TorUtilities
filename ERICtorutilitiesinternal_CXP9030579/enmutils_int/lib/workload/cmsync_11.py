from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class CMSYNC_11(PlaceHolderFlow):

    """
    Deprecated 21.11 To Be Deleted 22.07 JIRA: RTD-17599
    """

    NAME = "CMSYNC_11"

    def run(self):
        self.execute_flow()


cmsync_11 = CMSYNC_11()
