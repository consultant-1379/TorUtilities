from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting10Flow


class REPARENTING_10(Reparenting10Flow):
    """
    Use Case id:        REPARENTING_10
    Slogan:             Simulate a single user performing a request to determine the cut-over reparented cells for
                        450 cells.
    """

    NAME = "REPARENTING_10"

    def run(self):
        self.execute_flow()


reparenting_10 = REPARENTING_10()
