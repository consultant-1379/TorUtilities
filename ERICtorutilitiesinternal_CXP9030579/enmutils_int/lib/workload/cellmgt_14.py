from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ReadCellDataForDifferentNodes


class CELLMGT_14(ReadCellDataForDifferentNodes):
    """
    Use Case ID:    CELLMGT_14
    Slogan:         Geran Read Data
    """

    NAME = "CELLMGT_14"

    def run(self):
        self.execute_flow()


cellmgt_14 = CELLMGT_14()
