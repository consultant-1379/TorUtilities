from enmutils_int.lib.profile_flows.pm_flows.pmgpehprofile import PmGpehProfile


class PM_53(PmGpehProfile):

    """
    Use Case id:        PM_53
    Slogan:             GPEH Subscription & Event File Collection (RNC) with 1 min ROP
    """
    NAME = "PM_53"

    def run(self):
        self.execute_flow()


pm_53 = PM_53()
