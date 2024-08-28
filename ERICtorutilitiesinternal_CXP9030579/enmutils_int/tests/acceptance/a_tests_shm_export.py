#!/usr/bin/env python
import unittest2

from enmutils_int.lib.shm import SHMExport
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import func_dec, setup_verify


class ShmExportAcceptanceTests(unittest2.TestCase):
    SHM_EXPORT = None
    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["Shm_Administrator", "Cmedit_Administrator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        if not ShmExportAcceptanceTests.SHM_EXPORT:
            ShmExportAcceptanceTests.SHM_EXPORT = SHMExport(user=user, nodes=self.fixture.nodes)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec("SHM Export", "Export SHM Hardware to csv")
    def test_001_create_shm_export_csv(self):
        ShmExportAcceptanceTests.SHM_EXPORT.create()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
