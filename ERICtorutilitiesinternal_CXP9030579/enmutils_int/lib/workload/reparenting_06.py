from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting06Flow


class REPARENTING_06(Reparenting06Flow):
    """
    Use Case id:        REPARENTING_06
    Slogan:             Simulate a single user performing a request to determine the candidate cells for 450 cells.
    """

    NAME = "REPARENTING_06"

    def run(self):
        self.execute_flow()


reparenting_06 = REPARENTING_06()
