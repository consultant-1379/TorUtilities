from enmutils_int.lib.profile_flows.doc_flows.doc_flow import Doc01Flow


class DOC_01(Doc01Flow):
    """
    Use Case ID:        Doc_01
    Slogan:             Documentation Operator Load
    """
    NAME = "DOC_01"

    def run(self):
        self.execute_flow()


doc_01 = DOC_01()
