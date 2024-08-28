from enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile import PmStatisticalProfile


class PM_REST_NBI_01(PmStatisticalProfile):
    """
    Use Case ID:    PM_REST_NBI_01
    Slogan:         RadioNode Stats Subscription & File Collection
    """
    NAME = "PM_REST_NBI_01"

    def run(self):
        self.execute_flow(operations=["create", "activate", "deactivate", "delete"])


pm_rest_nbi_01 = PM_REST_NBI_01()
