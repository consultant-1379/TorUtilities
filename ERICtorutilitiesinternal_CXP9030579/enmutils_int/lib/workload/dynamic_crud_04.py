from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_04_flow import DynamicCrud04Flow


class DYNAMIC_CRUD_04(DynamicCrud04Flow):
    """
    Use Case ID:    DYNAMIC_CRUD_04
    Slogan:         Dynamic CM NBI CRUD Peak Node Reads
    """
    NAME = "DYNAMIC_CRUD_04"

    def run(self):
        self.execute_flow()


dynamic_crud_04 = DYNAMIC_CRUD_04()
