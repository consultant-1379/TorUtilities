from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow import CellMgt11


class CELLMGT_11(CellMgt11):
    """
    Use Case ID:    CELLMGT_11
    Slogan:         View LTE Cell Relations Data - 15 LTE Cells
    """

    NAME = "CELLMGT_11"

    def run(self):
        self.execute_cell_mgt_11_flow()


cellmgt_11 = CELLMGT_11()
