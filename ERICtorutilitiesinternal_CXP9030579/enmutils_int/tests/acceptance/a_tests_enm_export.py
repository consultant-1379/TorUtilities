#!/usr/bin/env python
import unittest2
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import func_dec, setup_verify

from enmutils_int.lib.enm_export import (CmExport, ShmExport)


class ExportAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}
    cm_export = None
    shm_export = None

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["Cmedit_Administrator", "CM_REST_Administrator", "Shm_Administrator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        if not self.cm_export and self.fixture.nodes and self.fixture.users:
            ExportAcceptanceTests.cm_export = CmExport(user=user, name='a_tests_cm_export', nodes=self.fixture.nodes)
            ExportAcceptanceTests.shm_export = ShmExport(nodes=self.fixture.nodes, user=self.fixture.users[0])

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("CM_EXPORT", "Create cm export job")
    @setup_verify(users=1)
    def test_001_job_create(self):
        ExportAcceptanceTests.cm_export.create()

    @func_dec("CM_EXPORT", "Verify export job")
    @setup_verify(users=1)
    def test_002_job_validate(self):
        ExportAcceptanceTests.cm_export.validate()

    @func_dec("CM_EXPORT", "Delete cm export job")
    @setup_verify(users=1)
    def test_003_job_delete(self):
        ExportAcceptanceTests.cm_export.delete()

    @func_dec("CM_EXPORT", "Create cm export over NBI job")
    @setup_verify(users=1)
    def test_007_job_create(self):
        ExportAcceptanceTests.cm_export.create_over_nbi()

    @func_dec("CM_EXPORT", "Verify export job")
    @setup_verify(users=1)
    def test_008_job_validate(self):
        ExportAcceptanceTests.cm_export.validate_over_nbi()

    @func_dec("CM_EXPORT", "Delete cm export job")
    @setup_verify(users=1)
    def test_009_job_delete(self):
        ExportAcceptanceTests.cm_export.delete()

    @func_dec("SHM_EXPORT", "Create shm export job")
    @setup_verify(users=1)
    def test_004_shm_job_create(self):
        ExportAcceptanceTests.shm_export.create()

    @func_dec("SHM_EXPORT", "Verify shm export job")
    @setup_verify(users=1)
    def test_005_shm_job_validate(self):
        ExportAcceptanceTests.shm_export.validate()

    @func_dec("SHM_EXPORT", "Delete shm export job")
    @setup_verify(users=1)
    def test_006_shm_job_delete(self):
        ExportAcceptanceTests.shm_export.delete()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
