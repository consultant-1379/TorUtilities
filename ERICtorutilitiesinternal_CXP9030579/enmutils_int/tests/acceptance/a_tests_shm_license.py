#!/usr/bin/env python
import time
import unittest2

from requests.exceptions import HTTPError

from enmutils_int.lib.shm_utilities import SHMLicense
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import func_dec, setup_verify


class ShmLicenseAcceptanceTests(unittest2.TestCase):
    SHM_LICENSE = None
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
        if not ShmLicenseAcceptanceTests.SHM_LICENSE:
            ShmLicenseAcceptanceTests.SHM_LICENSE = SHMLicense(user=user, node=self.fixture.nodes[0])

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec("SHM License", "Generate license key")
    def test_001_generate_license_key(self):
        ShmLicenseAcceptanceTests.SHM_LICENSE.generate()

    @setup_verify(available_nodes=1)
    @func_dec("SHM License", "Import license key")
    def test_003_import_license_key(self):
        ShmLicenseAcceptanceTests.SHM_LICENSE.import_keys()

    @setup_verify(available_nodes=1)
    @func_dec("SHM License", "Delete license key")
    def test_005_delete_license_key(self):
        try:
            ShmLicenseAcceptanceTests.SHM_LICENSE.delete()
        except HTTPError:
            # If the delete fails(usually with a fresh vApp), sleep and then retry
            time.sleep(3)
            ShmLicenseAcceptanceTests.SHM_LICENSE.delete()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
