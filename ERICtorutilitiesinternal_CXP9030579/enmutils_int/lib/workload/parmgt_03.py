from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_03_flow import ParMgt03Flow


class PARMGT_03(ParMgt03Flow):
    """
    Use Case ID:    ParameterManagement_03
    Slogan:         Generation of Bulk Import File
    """
    NAME = "PARMGT_03"

    def run(self):
        self.execute_flow()


parmgt_03 = PARMGT_03()
