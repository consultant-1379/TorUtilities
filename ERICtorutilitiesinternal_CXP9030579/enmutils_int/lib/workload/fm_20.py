from enmutils_int.lib.profile_flows.fm_flows.fm_20_flow import Fm20


class FM_20(Fm20):
    """
    Use Case ID:        FM_20
    Slogan:             Number of maximum number of users, 2 users performing FM UI tasks
    """

    NAME = "FM_20"

    def run(self):
        self.execute_flow_fm_20()


fm_20 = FM_20()
