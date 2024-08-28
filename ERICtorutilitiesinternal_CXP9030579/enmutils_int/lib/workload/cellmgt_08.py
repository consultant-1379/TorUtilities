from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import ViewAllLteCellsInTheNetwork


class CELLMGT_08(ViewAllLteCellsInTheNetwork):
    """
    Use Case ID:    CELLMGT_08
    Slogan:         View all LTE cells in the Network
    """

    NAME = "CELLMGT_08"

    def run(self):
        self.execute_flow()


cellmgt_08 = CELLMGT_08()
