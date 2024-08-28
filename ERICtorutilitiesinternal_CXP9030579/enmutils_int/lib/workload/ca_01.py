from enmutils_int.lib.profile_flows.ca_flows.ca_01_flow import CA01Flow


class CA_01(CA01Flow):
    """
    Use Case ID:    CA_01
    Slogan:         Consistency Audit
    """
    NAME = "CA_01"

    def run(self):
        self.execute_flow()


ca_01 = CA_01()
