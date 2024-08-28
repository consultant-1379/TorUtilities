from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ReadCellDataForDifferentNodes


class CELLMGT_09(ReadCellDataForDifferentNodes):
    """
    Use Case ID:    CELLMGT_09
    Slogan:         Read data from different node sets in parallel
    """

    NAME = "CELLMGT_09"

    def run(self):
        self.execute_flow()


cellmgt_09 = CELLMGT_09()
