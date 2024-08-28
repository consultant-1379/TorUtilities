from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting12Flow


class REPARENTING_12(Reparenting12Flow):
    """
    Use Case id:        REPARENTING_12
    Slogan:             Simulate a single user performing a request to determine the delete candidate cells for
                        450 cells.
    """

    NAME = "REPARENTING_12"

    def run(self):
        self.execute_flow()


reparenting_12 = REPARENTING_12()
