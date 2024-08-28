from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_02_flow import ParMgt02Flow


class PARMGT_02(ParMgt02Flow):
    """
    Use Case ID:    ParameterManagement_02
    Slogan:         Creation of Parameter Set
    """
    NAME = "PARMGT_02"

    def run(self):
        self.execute_flow()


parmgt_02 = PARMGT_02()
