from enmutils_int.lib.profile_flows.amos_flows.amos_logs_crontab_flow import Amos09Flow


class AMOS_09(Amos09Flow):
    """
    Use Case id:        AMOS_09
    Slogan:             AMOS Housekeeping.
    """

    NAME = "AMOS_09"

    def run(self):
        self.execute_flow()


amos_09 = AMOS_09()
