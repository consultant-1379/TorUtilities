from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting08Flow


class REPARENTING_08(Reparenting08Flow):
    """
    Use Case id:        REPARENTING_08
    Slogan:             Simulate a single user performing a request to determine determine-reparented-relations?
                        relationTypes=INTER_RAT for 450 cells.
    """

    NAME = "REPARENTING_08"

    def run(self):
        self.execute_flow()


reparenting_08 = REPARENTING_08()
