#!/usr/bin/env python
import copy
from random import choice

import unittest2

from enmutils.lib import shell, thread_queue
from enmutils_int.lib import enm_deployment
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec

REMOTE_TEST_USER = "cloud-user"


class RemoteShellAcceptanceTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        if not hasattr(self, "remote_test_host"):
            self.remote_test_host = enm_deployment.get_service_ip("pmserv")

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("Shell Library", "Run remote command that produces extra large output")
    def test_running_remote_command_producing_large_response(self):
        cmd = shell.Command("tail -10000 /var/spool/mail/netsim", timeout=60)
        resp = shell.run_remote_cmd(cmd, "netsim", "netsim", "netsim")
        self.assertEqual(0, resp.rc)

    @func_dec("Shell Library", "Large number of threads can share small number of connections in connection pool")
    def test_large_number_of_threads_can_share_connections_via_connection_pool(self):
        cmd = shell.Command("hostname", timeout=10)

        # Figure out the remote hostname, for reference
        hostname = shell.run_remote_cmd(cmd, "netsim", "netsim", "netsim").stdout

        def worker(cmd):
            return shell.run_remote_cmd(cmd, "netsim", "netsim", "netsim")

        shell.MAX_CONNECTIONS_PER_REMOTE_HOST = 3
        work_items = [copy.copy(cmd) for _ in range(0, 50)]
        tq = thread_queue.ThreadQueue(work_items, 10, worker)
        tq.execute()

        num_matches = 0

        for work_item in tq.work_entries:
            if work_item.result is not None and work_item.result.stdout is not None and work_item.result.stdout == hostname:
                num_matches += 1

        self.assertEqual(50, num_matches)

    @func_dec("Shell Library", "Execute commands on a remote host as different users")
    def test_successful_remote_command_with_different_users(self):
        cmd = shell.Command("whoami", timeout=10)
        resp = shell.run_remote_cmd(cmd, "netsim", "netsim", "netsim")
        self.assertEqual("netsim", resp.stdout.strip())

        resp = shell.run_remote_cmd(cmd, "netsim", "root", "shroot")
        self.assertEqual("root", resp.stdout.strip())

    @func_dec("Shell Library", "Execute commands on a remote host as different users")
    def test_successful_remote_command_with_different_users_when_pool_is_full(self):
        shell.MAX_CONNECTIONS_PER_REMOTE_HOST = 1
        cmd = shell.Command("whoami", timeout=10)
        resp = shell.run_remote_cmd(cmd, "netsim", "netsim", "netsim")
        self.assertEqual("netsim", resp.stdout.strip())

        resp = shell.run_remote_cmd(cmd, "netsim", "root", "shroot")
        self.assertEqual("root", resp.stdout.strip())

    @func_dec("Shell Library", "Execute commands on a remote host as different users")
    def test_successful_remote_command_with_different_users_when_pool_is_full_and_needs_to_wait_for_available_connection(self):
        shell.MAX_CONNECTIONS_PER_REMOTE_HOST = 5
        cmd = shell.Command("sleep 2", timeout=11)

        def worker(cmd):
            user = [('netsim', 'netsim')] * 10
            user.append(('root', 'shroot'))
            return shell.run_remote_cmd(cmd, 'netsim', *choice(user))

        work_items = [copy.copy(cmd) for _ in range(0, 10)]
        tq = thread_queue.ThreadQueue(work_items, 5, worker)
        tq.execute()

        cmd = shell.Command("whoami", timeout=10)
        resp = shell.run_remote_cmd(cmd, "netsim", "root", "shroot")
        self.assertEqual("root", resp.stdout.strip())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
