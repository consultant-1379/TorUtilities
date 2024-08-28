from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class ESM_02(PlaceHolderFlow):
    """
    Use Case ID:        ESM_02
    Slogan:             Number of Metrics Collected by Monitoring Tool
    """
    NAME = "ESM_02"

    def run(self):
        self.execute_flow()


esm_02 = ESM_02()
