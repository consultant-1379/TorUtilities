from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_01_flow import DynamicCrud01Flow


class DYNAMIC_CRUD_01(DynamicCrud01Flow):
    """
    Use Case ID:    DYNAMIC_CRUD_01
    Slogan:         Dynamic CM NBI CRUD Constant Cell Based requests
    """
    NAME = "DYNAMIC_CRUD_01"

    def run(self):
        """
        Call the flow of the profile
        """
        self.execute_flow()


dynamic_crud_01 = DYNAMIC_CRUD_01()
