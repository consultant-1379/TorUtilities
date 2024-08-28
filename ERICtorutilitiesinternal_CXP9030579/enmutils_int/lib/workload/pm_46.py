from enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile import PmGpehProfile


class PM_46(PmGpehProfile):
    """
    Use Case ID:    PM_46
    Slogan:         RNC GPEH Event Subscription & File Collection
    """
    NAME = "PM_46"

    def run(self):
        self.execute_flow()


pm_46 = PM_46()
