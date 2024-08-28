from enmutils_int.lib.profile_flows.pm_flows.pmrttsubscription import PmRTTSubscription


class PM_81(PmRTTSubscription):

    """
    Use Case id:        PM_81
    Slogan:             RTT Subscription for BSC Events
    """

    NAME = "PM_81"

    def run(self):
        self.execute_flow()


pm_81 = PM_81()
