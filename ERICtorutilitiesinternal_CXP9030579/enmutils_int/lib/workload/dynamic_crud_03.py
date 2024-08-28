from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_03_flow import DynamicCrud03Flow


class DYNAMIC_CRUD_03(DynamicCrud03Flow):
    """
    Use Case ID:    DYNAMIC_CRUD_03
    Slogan:         Dynamic CM NBI CRUD Create, Update, Delete
    """
    NAME = "DYNAMIC_CRUD_03"

    def run(self):
        self.execute_flow()


dynamic_crud_03 = DYNAMIC_CRUD_03()
