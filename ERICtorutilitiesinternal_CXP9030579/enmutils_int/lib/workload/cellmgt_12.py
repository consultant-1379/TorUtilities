from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_11_flow import CellMgt12


class CELLMGT_12(CellMgt12):
    """
    Use Case ID:    CELLMGT_12
    Slogan:         View WCDMA Cell Relations Data - 15 UtranCells
    """

    NAME = "CELLMGT_12"

    def run(self):
        self.execute_cell_mgt_11_flow()


cellmgt_12 = CELLMGT_12()
