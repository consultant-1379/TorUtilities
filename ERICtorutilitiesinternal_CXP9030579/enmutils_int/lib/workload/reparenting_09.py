from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting09Flow


class REPARENTING_09(Reparenting09Flow):
    """
    Use Case id:        REPARENTING_09
    Slogan:             Simulate a single user performing a request to determine the cut-over candidate cells for
                        450 cells.
    """

    NAME = "REPARENTING_09"

    def run(self):
        self.execute_flow()


reparenting_09 = REPARENTING_09()
