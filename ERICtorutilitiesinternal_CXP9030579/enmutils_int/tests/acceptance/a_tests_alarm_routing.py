#!/usr/bin/env python
import unittest2

from enmutils_int.lib.alarm_routing import AlarmRoutePolicy

from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify, func_dec


class AlarmRoutePolicyAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 3}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ['ADMINISTRATOR']

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        self.alarm_policy = AlarmRoutePolicy(user=user, name="acceptance_test_policy", nodes=self.fixture.nodes, description="acceptance_test")

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=3)
    @func_dec("Alarm Route Policy", "Create alarm route policy")
    def test_010_alarm_route_policy_create(self):
        self.alarm_policy.create()

    @setup_verify(available_nodes=3)
    @func_dec("Alarm Route Policy", "Disable and Enable alarm route policy")
    def test_020_alarm_route_policy_disable_and_enable(self):
        self.alarm_policy.disable()
        self.alarm_policy.enable()

    @setup_verify(available_nodes=3)
    @func_dec("Alarm Route Policy", "Delete alarm route policy")
    def test_030_alarm_route_policy_delete(self):
        self.alarm_policy.disable()
        self.alarm_policy.delete()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
