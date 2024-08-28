from enmutils_int.lib.profile_flows.pm_flows.pmcelltrafficprofile import PmCelltrafficProfile


class PM_29(PmCelltrafficProfile):
    """
    Use Case ID:    PM_29
    Slogan:         RNC CTR Subscription & File Collection
    """

    NAME = "PM_29"

    def run(self):
        self.execute_flow()


pm_29 = PM_29()
