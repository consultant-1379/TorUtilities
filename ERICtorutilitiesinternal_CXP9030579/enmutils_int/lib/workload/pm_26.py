from enmutils_int.lib.profile_flows.pm_flows.pm_fls_nbi_profile import PmFlsNbiProfile


class PM_26(PmFlsNbiProfile):
    """
    Use Case ID:    PM_26
    Slogan:         PMIC FLS (NBI)
    """
    NAME = "PM_26"

    def run(self):
        self.execute_flow()


pm_26 = PM_26()
