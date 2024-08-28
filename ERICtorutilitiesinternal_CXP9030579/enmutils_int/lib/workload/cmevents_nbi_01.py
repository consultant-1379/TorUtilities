from enmutils_int.lib.profile_flows.cmevents_flows.cmevents_nbi_01_flow import CmEventsNbi01


class CMEVENTS_NBI_01(CmEventsNbi01):
    """
    Use Case ID:    CMEVENTS_NBI_01
    Slogan:         Supported concurrent clients
    """

    NAME = "CMEVENTS_NBI_01"
    URL = '/config-mgmt/event/events?orderBy=eventDetectionTimestamp desc&limit={limit}'

    def run(self):
        self.execute_flow()


cmevents_nbi_01 = CMEVENTS_NBI_01()
