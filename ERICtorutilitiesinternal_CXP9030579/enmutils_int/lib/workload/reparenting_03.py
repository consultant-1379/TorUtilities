from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting03Flow


class REPARENTING_03(Reparenting03Flow):
    """
    Use Case id:        REPARENTING_03
    Slogan:             Simulate a single user performing a request to determine the candidate cells to be
                        deleted for 450 cells.
    """

    NAME = "REPARENTING_03"

    def run(self):
        self.execute_flow()


reparenting_03 = REPARENTING_03()
