from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ExecuteModifyCellParameters


class CELLMGT_01(ExecuteModifyCellParameters):
    """
    Use Case ID:    CELLMGT_01
    Slogan:         Modify existing cell and relation data
    """

    NAME = "CELLMGT_01"

    def run(self):
        self.execute_flow()


cellmgt_01 = CELLMGT_01()
