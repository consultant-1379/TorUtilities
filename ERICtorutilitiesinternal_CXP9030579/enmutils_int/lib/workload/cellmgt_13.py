from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import CreateAndDeleteCells


class CELLMGT_13(CreateAndDeleteCells):
    """
    Use Case ID:    CELLMGT_13
    Slogan:         Create/Delete 300 inter (ExternalGeranCellRelation) BSC relations using CGI Object (relations to
                    cells on another BSC)
    """

    NAME = "CELLMGT_13"

    def run(self):
        self.execute_flow()


cellmgt_13 = CELLMGT_13()
