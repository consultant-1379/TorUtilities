from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting11Flow


class REPARENTING_11(Reparenting11Flow):
    """
    Use Case id:        REPARENTING_11
    Slogan:             Simulate a single user performing a request to determine the customize-reparented cells for
                        450 cells.
    """

    NAME = "REPARENTING_11"

    def run(self):
        self.execute_flow()


reparenting_11 = REPARENTING_11()
