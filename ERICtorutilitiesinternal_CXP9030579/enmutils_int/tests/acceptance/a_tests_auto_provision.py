import os
import time
import shutil
import unittest2

from enmutils_int.lib.auto_provision import AutoProvision
from enmutils_int.lib.auto_provision_project import Project
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils.lib import filesystem, arguments, log
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify


class AutoProvisionAcceptanceTests(unittest2.TestCase):

    DESC = "Acceptance test project"
    PROJECT_NAME = "acceptance_test_project_{0}".format(arguments.get_random_string(4))
    NUM_NODES = {'RadioNode': 1}
    EXCLUSIVE = True

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
        self.user = self.fixture.users[0]
        self.project = Project(user=self.user, name=self.PROJECT_NAME, description=self.DESC, nodes=self.fixture.nodes)
        file_dir = "{0}.zip".format(self.project.PACKAGES.get('RadioNode')[0])
        source_dir = get_internal_file_path_for_import("etc", "data", file_dir)
        destination_dir = os.path.join("/home", "enmutils", "ap")
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        if os.path.exists(source_dir):
            shutil.copy(source_dir, destination_dir)
            shutil.copystat(source_dir, destination_dir)
        self.path = os.path.join(destination_dir, file_dir)
        self.project.create_project()
        self.auto = AutoProvision(user=self.user, project_name=self.PROJECT_NAME, nodes=self.project.nodes)
        self.node = self.project.nodes[0]

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    def test_01_create_project(self):
        self.project.create_project()

    def test_02_import_project(self):
        self.auto.delete_nodes_from_enm(user=self.user, nodes=self.fixture.nodes)
        self.auto.import_project(file_name="{0}.zip".format(self.PROJECT_NAME))
        time.sleep(60)
        self.assertTrue(self.auto.exists())

    def test_03_view_all(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.view(view_all=True)))

    def test_04_view_project(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.view()))

    def test_05_view_node(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.view(node=self.node)))

    def test_06_status_all(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.status(status_all=True)))

    def test_07_status_project(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.status()))

    def test_08_status_node(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.status(node=self.node)))

    def test_09_download_artifact(self):
        self.assertFalse(self.assertRaises(Exception, self.auto.download_artifacts(artifact="RADIONODE")))

    @unittest2.skip("Skipping until RTD-20425 completed.")
    def test_10_delete_project(self):
        try:
            self.auto.delete_project()
        finally:
            try:
                self.auto.create_and_supervise_node(self.node)
            except Exception as e:
                log.logger.debug("Encountered exception with populate operation: %s" % e.message)
            if filesystem.does_file_exist(self.path):
                filesystem.delete_file(self.path)
        self.assertFalse(self.auto.exists())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
