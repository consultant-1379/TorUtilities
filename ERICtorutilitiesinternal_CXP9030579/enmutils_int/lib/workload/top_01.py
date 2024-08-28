from enmutils_int.lib.profile_flows.top_flows.top_01_flow import TOP01Flow


class TOP_01(TOP01Flow):
    """
    Use Case ID:        TOP_01
    Slogan:             Topology Browser Operator Load.
    """

    NAME = "TOP_01"

    def run(self):
        self.execute_flow()


top_01 = TOP_01()
