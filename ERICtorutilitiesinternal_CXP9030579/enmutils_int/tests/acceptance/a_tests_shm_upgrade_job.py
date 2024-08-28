#!/usr/bin/env python
import os
import shutil

import unittest2
from enmutils.lib import log, filesystem
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.shm_utilities import SoftwarePackage, UpgradeJob
from enmutils_int.lib.shm_software_ops import SoftwareOperations
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import setup_verify, func_dec


class ShmUpgradeJobAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}
    upgrade_job = None
    software_operator = None
    zip_name = None
    software_package = None

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
        if self.fixture.nodes and self.fixture.users:
            self.software_package = SoftwarePackage(nodes=self.fixture.nodes, user=self.fixture.users[0],
                                                    mim_version="G1288", existing_package="CXPL16BCP1_G1288")
            self.software_package.new_package = "CXPL16BCP1_G1288"
            source_dir = get_internal_file_path_for_import("etc", "data", "CXPL16BCP1_G1288.zip")
            self.software_package.LOCAL_PATH = os.path.join("/home", "enmutils", "shm")
            if not os.path.exists(self.software_package.LOCAL_PATH):
                os.makedirs(self.software_package.LOCAL_PATH)
            if os.path.exists(source_dir):
                filesystem.copy(source_dir, self.software_package.LOCAL_PATH)
                shutil.copystat(source_dir, self.software_package.LOCAL_PATH)
            self.software_package.new_dir = os.path.join("/home", "enmutils", "shm", "CXPL16BCP1_G1288")
            self.software_operator = SoftwareOperations(user=user, package=self.software_package)
            self.zip_name = self.software_package.new_package
            try:
                self.software_operator.import_package()
            except Exception as e:
                log.logger.debug("Failed to import software package: {}".format(e.message))
            self.upgrade_job = UpgradeJob(user=user, nodes=self.fixture.nodes, software_package=self.software_package)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("SHM", "Create Upgrade Job")
    def test_001_create_upgrade_job(self):
        try:
            self.software_package.update_file_details_and_create_archive()
        except Exception as e:
            log.logger.debug("Setup encountered an issue: {}".format(e.message))
        self.upgrade_job.create()
        try:
            self.upgrade_job.cancel()
            self.upgrade_job.delete()
        except Exception as e:
            log.logger.debug("Failed to clean up job. Response: {0}".format(e.message))

    @setup_verify(users=1)
    @func_dec("SHM", "Cancel Upgrade Job")
    def test_002_cancel_upgrade_job(self):
        try:
            self.upgrade_job.create()
        except Exception as e:
            log.logger.debug("Failed to create job. Response: {0}".format(e.message))
        self.upgrade_job.cancel()
        try:
            self.upgrade_job.delete()
        except Exception as e:
            log.logger.debug("Failed to delete job. Response: {0}".format(e.message))

    @setup_verify(users=1)
    @func_dec("SHM", "Delete Upgrade Job")
    def test_003_delete_upgrade_job(self):
        try:
            self.upgrade_job.create()
            self.upgrade_job.cancel()
        except Exception as e:
            log.logger.debug("Failed to create, cancel job for deletion. Response: {0}".format(e.message))
        self.upgrade_job.delete()
        try:
            self.software_operator.delete()
        except Exception as e:
            log.logger.debug("Failed to delete package: {0}".format(e.message))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
