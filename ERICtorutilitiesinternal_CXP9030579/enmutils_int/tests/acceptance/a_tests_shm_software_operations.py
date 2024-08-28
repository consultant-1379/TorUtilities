#!/usr/bin/env python
import os
import shutil
import time

import unittest2

from enmutils.lib import filesystem
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.shm_utilities import SoftwarePackage
from enmutils_int.lib.shm_software_ops import SoftwareOperations
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import func_dec


class ShmSoftwareOperationsAcceptanceTests(unittest2.TestCase):

    software_package = None
    NUM_NODES = {'RadioNode': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["Shm_Administrator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        self.software_package = SoftwarePackage(nodes=self.fixture.nodes, user=self.fixture.users[0],
                                                mim_version=self.fixture.nodes[0].mim_version,
                                                existing_package="CXP9024421_R2SM",
                                                file_paths=['nmsinfo.xml'])
        source_dir = get_internal_file_path_for_import("etc", "data", "CXP9024421_R2SM.zip")
        self.software_package.LOCAL_PATH = os.path.join("/home", "enmutils", "shm")
        if not os.path.exists(self.software_package.LOCAL_PATH):
            os.makedirs(self.software_package.LOCAL_PATH)
        if os.path.exists(source_dir):
            filesystem.copy(source_dir, self.software_package.LOCAL_PATH)
            shutil.copystat(source_dir, self.software_package.LOCAL_PATH)
        self.software_package.set_package_values()
        software_package = SoftwarePackage(nodes=self.fixture.nodes, user=self.fixture.users[0],
                                           mim_version=self.fixture.nodes[0].mim_version,
                                           existing_package="CXP9024421_R2SM")
        software_package.new_package = "CXP9024421_R2SM"
        software_package.new_dir = os.path.join("/home", "enmutils", "shm", "CXP9024421_R2SM")
        self.software_operator = SoftwareOperations(user=user, package=software_package)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("SHM", "Import software package")
    def test_001_import_software_package(self):
        self.software_operator.import_package()
        time.sleep(5)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
