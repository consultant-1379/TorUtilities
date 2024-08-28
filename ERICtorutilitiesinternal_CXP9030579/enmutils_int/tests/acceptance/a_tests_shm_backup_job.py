#!/usr/bin/env python
import unittest2

from enmutils_int.lib.shm_backup_jobs import BackupJobCPP
from testslib import test_fixture, func_test_utils
from testslib.func_test_utils import setup_verify, func_dec


class ShmBackupJobAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}
    backup_job = None

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
        if not ShmBackupJobAcceptanceTests.backup_job:
            if self.fixture.nodes and self.fixture.users:
                ShmBackupJobAcceptanceTests.backup_job = BackupJobCPP(user=user,
                                                                      nodes=self.fixture.nodes,
                                                                      description='Backup job acceptance testing',
                                                                      schedule_time="00:00:00")

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("SHM", "Create Backup Job")
    def test_001_create_backup_job(self):
        ShmBackupJobAcceptanceTests.backup_job.create()

    @setup_verify(users=1)
    @func_dec("SHM", "Cancel Backup Job")
    def test_002_cancel_backup_job(self):
        ShmBackupJobAcceptanceTests.backup_job.cancel(verify_cancelled=False)

    @setup_verify(users=1)
    @func_dec("SHM", "Delete Backup Job")
    def test_003_delete_backup_job(self):
        ShmBackupJobAcceptanceTests.backup_job.delete()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
