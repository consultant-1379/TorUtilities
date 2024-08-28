from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting07Flow


class REPARENTING_07(Reparenting07Flow):
    """
    Use Case id:        REPARENTING_07
    Slogan:             Simulate a single user performing a request to determine the candidate cells for 450 cells.
                        INTRA_RAT Relations
    """

    NAME = "REPARENTING_07"

    def run(self):
        self.execute_flow()


reparenting_07 = REPARENTING_07()
