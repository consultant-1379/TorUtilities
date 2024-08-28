from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class PM_28(PlaceHolderFlow):
    """
    Deprecated in 24.09 and to be deleted in 25.04  ENMRTD-25370
    """
    NAME = "PM_28"

    def run(self):
        self.execute_flow()


pm_28 = PM_28()
