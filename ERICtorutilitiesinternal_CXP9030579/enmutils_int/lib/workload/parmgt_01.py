from enmutils_int.lib.profile_flows.parmgt_flows.parmgt_flow import ParMgt01Flow


class PARMGT_01(ParMgt01Flow):
    """
    Use Case ID:    ParameterManagement_01
    Slogan:         14 users concurrently modifying 2 attributes of simple data type on 100 MO instances
    """
    NAME = "PARMGT_01"

    def run(self):
        self.execute_flow()


parmgt_01 = PARMGT_01()
