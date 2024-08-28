#!/usr/bin/env python

import unittest2

from enmutils_int.lib.services import usermanager_adaptor
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec


class UserManagerAcceptanceTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.profile_name = "TEST_PROFILE_ACC"

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("UserManager Service", "Check if users can be successfully created using service "
                                     "and same users can execute CM CLI commands")
    def test_01_users_can_be_created_via_service_and_same_users_can_successfully_execute_cmedit_commands(self):
        users = usermanager_adaptor.create_users_via_usermanager_service(self.profile_name, 2, ["ADMINISTRATOR"])

        for user in users:
            output = user.enm_execute("cmedit describe -ne=ERBS").get_output()

            if not any([line for line in output if "instance" in line]):
                raise Exception

    @func_dec("UserManager Service", "Check if users can be successfully listed using service")
    def test_02_user_listed_successfully(self):
        users = usermanager_adaptor.get_users_via_service(self.profile_name)

        if not (users and self.profile_name in users[0].username and self.profile_name in users[1].username):
            raise Exception

    @func_dec("UserManager Service", "Check if user can be successfully deleted using service")
    def test_03_user_can_be_deleted_via_service(self):
        usermanager_adaptor.delete_users_via_usermanager_service(self.profile_name)
        # Reliant on an actual ENM delete and no longer DB deletion
        import time
        time.sleep(10)
        if usermanager_adaptor.get_users_via_service(self.profile_name):
            raise Exception

    @func_dec("UserManager Service", "Check if users with different roles can be created successfully")
    def test_04_users_with_different_roles_can_be_created(self):
        usermanager_adaptor.create_users_via_usermanager_service(self.profile_name, 1, ["Cmedit_Operator"])
        # above users should be removed by next step and replace by different users with same set of roles
        usermanager_adaptor.create_users_via_usermanager_service(self.profile_name, 2, ["Cmedit_Operator"])

        usermanager_adaptor.create_users_via_usermanager_service(self.profile_name, 2, ["Cmedit_Operator",
                                                                                        "Cmedit_Administrator"])

        if len(usermanager_adaptor.get_users_via_service(self.profile_name)) != 4:
            raise Exception

        usermanager_adaptor.delete_users_via_usermanager_service(self.profile_name)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
