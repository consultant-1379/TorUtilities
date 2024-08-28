from enmutils_int.lib.profile_flows.reparenting_flows.reparenting_flow import Reparenting02Flow


class REPARENTING_02(Reparenting02Flow):
    """
    Use Case id:        REPARENTING_02
    Slogan:             Simulate a single user performing a request to determine impacts for 150 TGs
                        (assuming 3 cells per TG).
    """

    NAME = "REPARENTING_02"

    def run(self):
        self.execute_flow()


reparenting_02 = REPARENTING_02()
