from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting04Flow


class REPARENTING_04(Reparenting04Flow):
    """
    Use Case id:        REPARENTING_04
    Slogan:             Simulate a single user performing a request to determine the conflicting relations to be
                        created for 450 cells.
    """

    NAME = "REPARENTING_04"

    def run(self):
        self.execute_flow()


reparenting_04 = REPARENTING_04()
