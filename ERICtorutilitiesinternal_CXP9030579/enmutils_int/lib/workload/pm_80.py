from enmutils_int.lib.profile_flows.pm_flows.pmrpmosubscriptionprofile import PmRPMOSubscriptionProfile


class PM_80(PmRPMOSubscriptionProfile):

    """
    Use Case ID:    PM_80
    Slogan:         RPMO Subscription for BSC Events
    """
    NAME = "PM_80"

    def run(self):
        self.execute_flow()


pm_80 = PM_80()
