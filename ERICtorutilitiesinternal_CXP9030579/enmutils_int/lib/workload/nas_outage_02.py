from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_02 import NasOutage02Flow


class NAS_OUTAGE_02(NasOutage02Flow):
    """
    Use Case ID:    NAS_OUTAGE_02
    Slogan:    Intermittent NAS outage on a single instance
    """
    NAME = "NAS_OUTAGE_02"

    def run(self):
        self.execute_flow()


nas_outage_02 = NAS_OUTAGE_02()
