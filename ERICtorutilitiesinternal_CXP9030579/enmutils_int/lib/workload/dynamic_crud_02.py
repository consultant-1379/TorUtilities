from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_02_flow import DynamicCrud02Flow


class DYNAMIC_CRUD_02(DynamicCrud02Flow):
    """
    Use Case ID:    DYNAMIC_CRUD_02
    Slogan:         Dynamic CM NBI CRUD Constant Network wide requests
    """
    NAME = "DYNAMIC_CRUD_02"

    def run(self):
        self.execute_flow()


dynamic_crud_02 = DYNAMIC_CRUD_02()
