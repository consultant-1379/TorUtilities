from enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_02_flow import CmEventsNbi02


class CMEVENTS_NBI_02(CmEventsNbi02):
    """
    Use Case ID:    CMEVENTS_NBI_02
    Slogan: -   CM Events to NM subscribers
    """

    NAME = "CMEVENTS_NBI_02"

    def run(self):
        self.execute_flow()


cmevents_nbi_02 = CMEVENTS_NBI_02()
