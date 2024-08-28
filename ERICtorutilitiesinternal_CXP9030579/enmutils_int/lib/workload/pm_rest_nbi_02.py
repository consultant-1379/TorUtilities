from enmutils_int.lib.profile_flows.pm_flows.pmrestnbistatisticalprofile import PmStatisticalProfile


class PM_REST_NBI_02(PmStatisticalProfile):
    """
    Use Case ID:    PM_REST_NBI_02
    Slogan:         RadioNode Stats Subscription & File Collection

    """
    NAME = "PM_REST_NBI_02"

    def run(self):
        self.execute_flow(operations=["create", "delete"])


pm_rest_nbi_02 = PM_REST_NBI_02()
