from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_04_flow import ParMgt04Flow


class PARMGT_04(ParMgt04Flow):
    """
    Use Case ID:    PARMGT_04
    Slogan:         5 Users checking Transport Connectivity State
    """
    NAME = "PARMGT_04"

    def run(self):
        self.execute_flow()


parmgt_04 = PARMGT_04()
