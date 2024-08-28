from enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow import Fm0506


class FM_0506(Fm0506):
    """
    Use Case ID:        FM_05-07
    Slogan:             Setting up ENM for FM workload including ceasing all existing alarms and setting up delayed
                        and auto acknowledgements on the network
    """

    NAME = "FM_0506"

    def run(self):
        self.execute_fm_0506_normal_flow()


fm_0506 = FM_0506()
