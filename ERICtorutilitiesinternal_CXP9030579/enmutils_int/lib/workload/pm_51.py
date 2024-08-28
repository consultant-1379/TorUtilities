from enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile import PmGpehProfile


class PM_51(PmGpehProfile):
    """
    Use Case ID:    PM_51
    Slogan:         RNC GPEH Event Subscription & File Collection
    """
    NAME = "PM_51"

    def run(self):
        self.execute_flow()


pm_51 = PM_51()
