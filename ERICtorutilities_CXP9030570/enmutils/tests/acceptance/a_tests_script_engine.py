#!/usr/bin/env python
import unittest2

from enmutils.lib.script_engine_2 import Request
from testslib import test_fixture, func_test_utils


class ScriptEngineAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["Cmedit_Administrator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        self.request = Request('cmedit get * NetworkElement', user=self.fixture.users[0])

    def tearDown(self):
        func_test_utils.tear_down(self)

    def test_job_execute(self):
        response = self.request.execute()
        self.assertIsNotNone(response.get_output())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
