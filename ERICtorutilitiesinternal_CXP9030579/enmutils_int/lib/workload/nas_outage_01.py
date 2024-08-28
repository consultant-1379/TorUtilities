from enmutils_int.lib.profile_flows.nas_outage_flows.nas_outage_01 import NasOutage01Flow


class NAS_OUTAGE_01(NasOutage01Flow):
    """
    Use Case ID:    NAS_OUTAGE_01
    Slogan:    NAS head outage
    """
    NAME = "NAS_OUTAGE_01"

    def run(self):
        self.execute_flow()


nas_outage_01 = NAS_OUTAGE_01()
