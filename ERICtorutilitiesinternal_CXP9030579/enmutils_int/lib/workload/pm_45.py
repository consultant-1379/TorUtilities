from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class PM_45(PlaceHolderFlow):
    """
    Deprecated in 24.09 and to be deleted in 25.04  ENMRTD-25370
    """

    NAME = "PM_45"

    def run(self):
        self.execute_flow()


pm_45 = PM_45()
