#!/usr/bin/env python
import time

import unittest2
from requests.exceptions import HTTPError

from enmutils_int.lib.nhm import NhmKpi
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec, setup_verify


class NhmKpiAcceptanceTests(unittest2.TestCase):

    kpi = None
    NUM_NODES = {'ERBS': 1}
    KPI_NAME = "acceptance_kpi"

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
        if not self.kpi:
            self.kpi = NhmKpi(name=self.KPI_NAME, reporting_objects=['ENodeBFunction'], nodes=self.fixture.nodes,
                              counters=["pmPagS1EdrxDiscarded", "pmPagS1Received"], active=False, node_types=['ERBS'],
                              user=user)

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("NHM", "Create KPI")
    def test_001_create_kpi(self):
        try:
            self.kpi.create()
            # KPI service can be slow to create the KPI instance
            time.sleep(30)
        except HTTPError:
            self.assertIsNotNone(self.kpi.get_kpi(user=self.fixture.users[0], name=[self.KPI_NAME]))
        else:
            self.assertIsNotNone(self.kpi.get_kpi(user=self.fixture.users[0], name=[self.KPI_NAME]))

    @setup_verify(users=1)
    @func_dec("NHM", "Activate KPI")
    def test_002_activate_kpi(self):
        self.kpi.activate()

    @setup_verify(users=1)
    @func_dec("NHM", "Deactivate KPI")
    def test_003_deactivate_kpi(self):
        self.kpi.deactivate()

    @setup_verify(users=1)
    @func_dec("NHM", "Update Formula KPI")
    def test_004_update_kpi(self):
        if self.kpi.get_kpi(user=self.fixture.users[0], name=[self.KPI_NAME]):
            self.kpi.update(replace_formula=True)

    @setup_verify(users=1)
    @func_dec("NHM", "Get KPI")
    def test_005_get_kpi_by_name(self):
        self.kpi.get_kpi_by_name(user=self.fixture.users[0], name=None)

    @setup_verify(users=1)
    @func_dec("NHM", "Delete KPI")
    def test_006_delete_kpi(self):
        self.kpi.delete()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
