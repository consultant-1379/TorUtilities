from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ExecuteModifyCellParameters


class CELLMGT_07(ExecuteModifyCellParameters):
    """
    Use Case ID:    CELLMGT_07
    Slogan:         Modify existing cell and relation data (WCDMA)
    """

    NAME = "CELLMGT_07"

    def run(self):
        self.execute_flow()


cellmgt_07 = CELLMGT_07()
