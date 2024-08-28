from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import CreateDeleteCellsAndRelationsFlow


class CELLMGT_03(CreateDeleteCellsAndRelationsFlow):
    """
    Use Case ID:    CELLMGT_03
    Slogan:         Create cell and relation data
    """
    NAME = "CELLMGT_03"

    def run(self):
        self.execute_flow()


cellmgt_03 = CELLMGT_03()
