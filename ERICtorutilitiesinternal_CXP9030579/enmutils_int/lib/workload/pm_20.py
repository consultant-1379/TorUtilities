from enmutils_int.lib.profile_flows.pm_flows.pmebmprofile import PmEBMProfile


class PM_20(PmEBMProfile):
    """
    Use Case ID:    PM_20
    Slogan:         EBM Subscription & File Collection 1 minute
    """
    NAME = "PM_20"

    def run(self):
        self.execute_flow()


pm_20 = PM_20()
