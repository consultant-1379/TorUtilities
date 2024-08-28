#!/usr/bin/env python
from datetime import datetime, timedelta
from random import randint, sample

import unittest2

from enmutils_int.lib.auto_id_management import ManualAutoIdProfile, OpenLoopAutoIdProfile, ClosedLoopAutoIdProfile, \
    TopologyGroupRange, NonPlannedPCIRange
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify, func_dec


class AutoIdManagement(unittest2.TestCase):
    manual_loop_profile = None
    open_loop_profile = None
    closed_loop_profile = None
    toplogy_group_range = None
    non_planned_pci_range = None

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)
        cls.fixture.num_users = 1
        cls.fixture.user_roles = ["ADMINISTRATOR"]

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        user = self.fixture.users[0]
        if not AutoIdManagement.manual_loop_profile:
            AutoIdManagement.manual_loop_profile = ManualAutoIdProfile(user=user, name="manual_acceptance_test", nodes=self.fixture.nodes)
        if not AutoIdManagement.open_loop_profile:
            AutoIdManagement.open_loop_profile = OpenLoopAutoIdProfile(user=user, name="open_acceptance_test", nodes=self.fixture.nodes)
        if not AutoIdManagement.closed_loop_profile:
            start_time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 23, 15, 0)
            closed_loop_times = [start_time + timedelta(hours=hour) for hour in xrange(0, 23, 12)]
            AutoIdManagement.closed_loop_profile = ClosedLoopAutoIdProfile(user=user, name="closed_acceptance_test", nodes=self.fixture.nodes,
                                                                           scheduled_times=closed_loop_times)
        if not AutoIdManagement.toplogy_group_range:
            AutoIdManagement.toplogy_group_range = TopologyGroupRange(user=user, name="topology_group_range_acceptance_test",
                                                                      first_pci_value_range={randint(2, 167): randint(0, 2)},
                                                                      nodes=self.fixture.nodes)
        if not AutoIdManagement.non_planned_pci_range:
            AutoIdManagement.non_planned_pci_range = NonPlannedPCIRange(user=user, frequency=sample([2110.1, 2110.2, 2110.3, 2110.4], 1)[0],
                                                                        pci_ranges={randint(2, 167): randint(0, 2)})

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Create Manual loop profile")
    def test_010_manual_loop_creation(self):
        AutoIdManagement.manual_loop_profile.create()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Delete Manual loop profile")
    def test_020_manual_loop_deletion(self):
        AutoIdManagement.manual_loop_profile.delete()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Create Open loop profile")
    def test_030_open_loop_creation(self):
        AutoIdManagement.open_loop_profile.create()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Delete Open loop profile")
    def test_040_open_loop_deletion(self):
        AutoIdManagement.open_loop_profile.delete()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Create Closed loop profile")
    def test_050_closed_loop_creation(self):
        AutoIdManagement.closed_loop_profile.create()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Delete Closed loop profile")
    def test_060_closed_loop_deletion(self):
        AutoIdManagement.closed_loop_profile.delete()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Create Topology Group range")
    def test_070_topology_group_range_creation(self):
        AutoIdManagement.toplogy_group_range.create()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Delete Topology Group range")
    def test_080_topology_group_range_deletion(self):
        AutoIdManagement.toplogy_group_range.delete()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Create Non-Planned PCI range")
    def test_090_non_planned_pci_range_creation(self):
        AutoIdManagement.non_planned_pci_range.create()

    @setup_verify(available_nodes=1)
    @func_dec("Auto Id Management", "Delete Non-Planned PCI range")
    def test_100_non_planned_pci_range_deletion(self):
        AutoIdManagement.non_planned_pci_range.delete()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
