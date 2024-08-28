from enmutils_int.lib.profile_flows.pm_flows.pm_eniq_flow2 import PmEniqFlow


class PM_44(PmEniqFlow):
    """
    Use Case ID:    PM_44
    Slogan:         ENIQ Statistics (ES) Integration with files read from FLS query.
    """
    NAME = "PM_44"

    def run(self):
        self.execute_flow()


pm_44 = PM_44()
