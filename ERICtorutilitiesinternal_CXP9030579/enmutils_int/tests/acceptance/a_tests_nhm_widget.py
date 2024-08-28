#!/usr/bin/env python
import unittest2

from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec, setup_verify

from enmutils_int.lib.services.deployment_info_helper_methods import build_poid_dict_from_enm_data

from enmutils_int.lib.nhm import NhmKpi, CREATED_BY_DEFAULT
from enmutils_int.lib.nhm_widget import NodesBreached, WorstPerforming, MostProblematic, NetworkOperationalState


class NhmWidgetAcceptanceTests(unittest2.TestCase):

    worst_widget = None
    breached_widget = None
    problematic_widget = None
    network_widget = None
    kpi = None
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
        nodes = self.fixture.nodes
        user = self.fixture.users[0]

        # updating nodes with poids
        node_poid_data = build_poid_dict_from_enm_data()
        nodes_verified_on_enm = []
        for node in nodes:
            node.poid = node_poid_data.get(node.node_id)
            nodes_verified_on_enm.append(node)
        node_poids = [node_poid_data[node.node_id] for node in nodes if node.poid]
        nodes = nodes_verified_on_enm

        #  We need an active KPI for widgets to be created
        NhmWidgetAcceptanceTests.kpi = NhmKpi(user=user,
                                              name="E-RAB_Retainability_eNB_Percentage_Lost",
                                              reporting_objects=['EUtranCellTDD', 'EUtranCellFDD'],
                                              nodes=[], node_types=['ERBS', 'RadioNode'],
                                              created_by=CREATED_BY_DEFAULT)
        NhmWidgetAcceptanceTests.kpi.update(add_nodes=node_poids)
        NhmWidgetAcceptanceTests.kpi.activate()

        NhmWidgetAcceptanceTests.worst_widget = WorstPerforming(user=user, nodes=nodes)
        NhmWidgetAcceptanceTests.breached_widget = NodesBreached(user=user, nodes=nodes, number_of_kpis=10)
        NhmWidgetAcceptanceTests.problematic_widget = MostProblematic(user=user, nodes=nodes)
        NhmWidgetAcceptanceTests.network_widget = NetworkOperationalState(user=user, nodes=nodes)

    def tearDown(self):
        NhmWidgetAcceptanceTests.kpi.deactivate()
        NhmWidgetAcceptanceTests.kpi.update(remove_all_nodes=True)
        func_test_utils.tear_down(self)

    @setup_verify(users=1)
    @func_dec("NHM", "Create Most Problematic Widget")
    def test_001_create_most_problematic_widget(self):
        NhmWidgetAcceptanceTests.problematic_widget.create()

    @setup_verify(users=1)
    @func_dec("NHM", "Create Network Operational State Widget")
    def test_002_create_network_state_widget(self):
        NhmWidgetAcceptanceTests.network_widget.create()

    @setup_verify(users=1)
    @func_dec("NHM", "Create Worst Performing Widget")
    def test_003_create_worst_performing_widget(self):
        NhmWidgetAcceptanceTests.worst_widget.create()

    @setup_verify(users=1)
    @func_dec("NHM", "Create Nodes Breached Widget")
    def test_004_create_nodes_breached_widget(self):
        NhmWidgetAcceptanceTests.breached_widget.create()

    @setup_verify(users=1)
    @func_dec("NHM", "Delete Most Problematic Widgets")
    def test_005_delete_most_problematic_widget(self):
        NhmWidgetAcceptanceTests.problematic_widget.delete()

    @setup_verify(users=1)
    @func_dec("NHM", "Delete Network Operational StateWidgets")
    def test_006_delete_network_state_widget(self):
        NhmWidgetAcceptanceTests.network_widget.delete()

    @setup_verify(users=1)
    @func_dec("NHM", "Delete Worts Performing Widgets")
    def test_007_delete_worst_performing_widget(self):
        NhmWidgetAcceptanceTests.worst_widget.delete()

    @setup_verify(users=1)
    @func_dec("NHM", "Delete Breached Widgets")
    def test_008_delete_breached_widget(self):
        NhmWidgetAcceptanceTests.breached_widget.delete()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
