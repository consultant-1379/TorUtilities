from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import CreateDeleteCellsAndRelationsFlow


class CELLMGT_05(CreateDeleteCellsAndRelationsFlow):
    """
    Use Case ID:    CELLMGT_05
    Slogan:         Create cell and relation data (WCDMA)
    """
    NAME = "CELLMGT_05"

    def run(self):
        self.execute_flow()


cellmgt_05 = CELLMGT_05()
