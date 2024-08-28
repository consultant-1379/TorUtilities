from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting01Flow


class REPARENTING_01(Reparenting01Flow):
    """
    Use Case id:        REPARENTING_01
    Slogan:             Simulate a single user performing a request to determine the candidate cells
                        for 150 TGs (assuming 3 cells per TG).
    """

    NAME = "REPARENTING_01"

    def run(self):
        self.execute_flow()


reparenting_01 = REPARENTING_01()
