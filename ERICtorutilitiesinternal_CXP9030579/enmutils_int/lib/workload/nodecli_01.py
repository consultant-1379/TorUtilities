from enmutils_int.lib.profile_flows.nodecli_flows.nodecli_01_flow import NodeCli01Flow


class NODECLI_01(NodeCli01Flow):
    """
    Use Case ID:    NODECLI_01
    Slogan:         Max number of users and sessions
    """

    NAME = "NODECLI_01"

    def run(self):
        self.execute_flow()


nodecli_01 = NODECLI_01()
