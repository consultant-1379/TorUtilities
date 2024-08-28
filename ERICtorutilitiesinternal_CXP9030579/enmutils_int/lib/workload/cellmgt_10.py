from enmutils_int.lib.profile_flows.cellmgt_flows.cellmgt_flow import LockUnlockAllCellsOnAnNode


class CELLMGT_10(LockUnlockAllCellsOnAnNode):
    """
    Use Case ID:    CELLMGT_10
    Slogan:         Lock/Unlock all cells on a node
    """

    NAME = "CELLMGT_10"

    def run(self):
        self.execute_flow()


cellmgt_10 = CELLMGT_10()
