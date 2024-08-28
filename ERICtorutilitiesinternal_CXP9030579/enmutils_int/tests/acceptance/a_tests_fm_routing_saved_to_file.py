#!/usr/bin/env python
from random import randint
from time import sleep
import unittest2
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec

from enmutils_int.lib.fm import FmAlarmRoute


class FmRoutingSavedToFilesAcceptanceTests(unittest2.TestCase):

    routing = None

    NUM_NODES = {'ERBS': 1}
    FILE_NAME = "AcceptanceTest{}".format(randint(0, 9999999999999))

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["FM_Administrator"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        self.routing = FmAlarmRoute(user, self.fixture.nodes, self.FILE_NAME, self.FILE_NAME)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("FM", "Create Routing Saved To File and delete it")
    def test_01_create_and_delete_routing(self):
        self.routing.create()
        sleep(0.2)
        self.routing.delete()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
