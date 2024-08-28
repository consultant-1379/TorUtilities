from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ExecuteModifyCellParameters


class CELLMGT_02(ExecuteModifyCellParameters):
    """
    Use Case ID:    CELLMGT_02
    Slogan:         Modify existing cell and relation data
    """

    NAME = "CELLMGT_02"

    def run(self):
        self.execute_flow()


cellmgt_02 = CELLMGT_02()
