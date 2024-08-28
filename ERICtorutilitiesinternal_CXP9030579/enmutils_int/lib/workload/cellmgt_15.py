from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import LockUnlockAllCellsOnAnNode


class CELLMGT_15(LockUnlockAllCellsOnAnNode):
    """
    Use Case ID:    CELLMGT_15
    Slogan:         Lock/Unlock 3 Cells on 40 BSC Nodes.
    """

    NAME = "CELLMGT_15"

    def run(self):
        self.execute_flow()


cellmgt_15 = CELLMGT_15()
