from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting05Flow


class REPARENTING_05(Reparenting05Flow):
    """
    Use Case id:        REPARENTING_05
    Slogan:             Simulate a single user performing a request to determine the conflicting relations to be
                        deleted for 450 cells.
    """

    NAME = "REPARENTING_05"

    def run(self):
        self.execute_flow()


reparenting_05 = REPARENTING_05()
