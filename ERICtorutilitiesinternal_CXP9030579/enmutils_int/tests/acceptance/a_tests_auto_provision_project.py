import os
import shutil
import unittest2
from enmutils.lib import arguments
from enmutils_int.lib.auto_provision_project import Project, scp_upgrade_packages
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify


class AutoProvisionProjectAcceptanceTests(unittest2.TestCase):

    DESC = "Acceptance test project"
    PROJECT_NAME = "acceptance_test_project_{0}".format(arguments.get_random_string(4))
    NUM_NODES = {'RadioNode': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        self.project = Project(user=user, name=self.PROJECT_NAME, description=self.DESC,
                               nodes=self.fixture.nodes)

    def tearDown(self):
        path = os.path.join("/home", "enmutils", "ap", "{0}.zip".format(self.PROJECT_NAME))
        if os.path.exists(path):
            shutil.rmtree(path)
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    def test_create_project(self):
        try:
            scp_upgrade_packages(use_proxy=False)
        except Exception:
            pass
        self.assertEqual(None, self.project.create_project())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
