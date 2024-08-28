#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock

from enmutils.lib.exceptions import EnvironError, NoOuputFromScriptEngineResponseError, ScriptEngineResponseValidationError
from testslib import unit_test_utils
from enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow import Nhm0102, HTTPError


class Nhm02UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.mock_node = Mock()
        self.mock_node.primary_type = 'ERBS'
        self.mock_node.node_id = 'some_node_id'
        self.counters = ['counter_01', 'counter_02']
        self.usable_kpis = {'ERBS': [u'Abnormal_Releases_ENB'],
                            'RadioNode': [u'Abnormal_Releases_ENB', u'Abnormal_Releases_MME', u'Active_Downlink_Users'],
                            'RNC': [u'Abnormal_Releases_ENB', u'Abnormal_Releases_MME', u'Active_Downlink_Users']}

        self.flow = Nhm0102()
        self.flow.TRANSPORT_SETUP = False
        self.flow.supported_node_types = ["ERBS", "RadioNode", "RNC"]
        self.flow.USER_ROLES = ["NHM_Administrator"]
        self.flow.REPORTING_OBJECT_01 = {'ERBS': 'ENodeBFunction', 'RadioNode': 'ENodeBFunction'}
        self.flow.REPORTING_OBJECT_02 = {'RNC': ['UtranCell'], 'ERBS': ['EUtranCellFDD', 'EUtranCellTDD'],
                                         'RadioNode': ['EUtranCellFDD', 'EUtranCellTDD']}
        self.flow.REPORTING_OBJECT = ['global', 'dot1q-history', 'port-history', 'link-group-history']
        self.flow.MAX_NUMBER_OF_CUSTOM_KPIS = 50
        self.flow.NUM_NODES = {'RNC': 1, 'ERBS': 10, 'RadioNode': -1}
        self.flow.UNSUPPORTED_KPIS = ['test_kpi_2']
        self.flow.NUM_KPIS_01 = 7
        self.flow.NUMBER_OF_INSTANCES_REQUIRED = 1320000.0
        self.flow.SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI = ['RNC', 'ERBS', 'RadioNode']
        self.flow.UNSUPPORTED_TYPES_NODE_LEVEL_KPI = ['RNC']
        self.flow.custom_kpis_to_create = {'ERBS': 1, 'RadioNode': 3, 'RNC': 3}

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102._clean_system_nhm_02')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102._clean_system_nhm_01')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.calculate_expected_kpi_instances')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    def test_execute_flow_success__not_transport(self, mock_get_nodes, mock_create_profile_users,
                                                 mock_calculate_expected, mock_clean_nhm_01, mock_clean_nhm_02, *_):
        mock_calculate_expected.return_value = self.flow.custom_kpis_to_create, self.usable_kpis
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = ["100 instance(s)"]
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_get_nodes.return_value = [self.mock_node]

        with patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.execute_flow_nhm_01') as mock_execute_nhm_01:
            with patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.execute_flow_nhm_02') as mock_execute_nhm_02:
                self.flow.execute_flow()
                self.assertTrue(mock_clean_nhm_01.called)
                self.assertTrue(mock_clean_nhm_02.called)
                self.assertTrue(mock_execute_nhm_01.called)
                self.assertTrue(mock_execute_nhm_02.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.track_kpi_creation')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    def test_execute_flow_success_with_new_kpis_added(self, mock_nhm_kpi, mock_get_nodes,
                                                      mock_create_profile_users, *_):
        mock_nhm_kpi.get_counters_specified_by_nhm.return_value = ['counter1', 'counter2']
        mock_kpi_object = Mock()
        mock_nhm_kpi.return_value = mock_kpi_object
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = ["100 instance(s)"]
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_get_nodes.return_value = [self.mock_node]

        self.flow.execute_flow()
        self.assertTrue(mock_nhm_kpi.get_counters_specified_by_nhm.called)
        self.assertTrue(mock_kpi_object.create.called)
        self.assertTrue(mock_kpi_object.create.activate)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.track_kpi_creation')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.'
           'calculate_the_total_number_of_kpi_instances_avaiable')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    def test_execute_flow_success_with_removed_kpis(self, mock_nhm_kpi, mock_caculate_number, mock_get_nodes,
                                                    mock_create_profile_users, *_):
        mock_nhm_kpi.get_counters_specified_by_nhm.return_value = ['counter1', 'counter2']
        mock_kpi_object = Mock()
        mock_nhm_kpi.return_value = mock_kpi_object
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = ["100 instance(s)"]
        mock_user = Mock()
        mock_user.enm_execute.return_value = mock_enm_response
        mock_create_profile_users.return_value = [mock_user]
        mock_caculate_number.return_value = self.flow.NUMBER_OF_INSTANCES_REQUIRED
        mock_get_nodes.return_value = [self.mock_node]

        self.flow.execute_flow()
        self.assertTrue(mock_nhm_kpi.get_counters_specified_by_nhm.called)
        self.assertTrue(mock_kpi_object.create.called)
        self.assertTrue(mock_kpi_object.create.activate)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.execute_flow_nhm_02')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.calculate_expected_kpi_instances')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.execute_flow_nhm_01')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    def test_execute_flow__exception_creating_cell_level_kpis(self, mock_get_nodes, mock_execute_nhm_01, mock_calculate,
                                                              mock_execute_nhm_02, mock_add_error, *_):
        mock_get_nodes.return_value = [self.mock_node]
        mock_calculate.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_execute_nhm_01.called)
        self.assertFalse(mock_execute_nhm_02.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    def test_execute_flow_failure_no_nodes_verified_on_enm(self, mock_get_nodes, mock_log, *_):
        mock_get_nodes.return_value = None

        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    def test_execute_flow_failure_exception_while_cleaning_the_system(self, mock_get_nodes, mock_log, mock_kpi, *_):
        mock_get_nodes.return_value = None
        mock_kpi.remove_kpis_by_pattern_new.side_effect = Exception()
        mock_kpi.clean_down_system_kpis.side_effect = Exception()
        self.flow.execute_flow()
        self.assertTrue(mock_log.logger.debug.called)

    def test_calculate_the_total_number_of_kpi_instances_avaiable__no_cells(self):
        node_cell_dict = {'ERBS': {'number_of_nodes': 5, 'number_of_cells': 0},
                          'RadioNode': {'number_of_nodes': 5, 'number_of_cells': 0},
                          'RNC': {'number_of_nodes': 1, 'number_of_cells': 0}}
        self.assertRaises(EnvironError, self.flow.calculate_the_total_number_of_kpi_instances_avaiable,
                          self.flow.MAX_NUMBER_OF_CUSTOM_KPIS, node_cell_dict, self.usable_kpis)

    def test_reduce_number_of_kpis(self):
        number_of_cells_per_node = {'ERBS': {'number_of_cells': 1000}, 'RNC': {'number_of_cells': 1000},
                                    'RadioNode': {'number_of_cells': 1000}}
        self.flow.reduce_number_of_kpis(self.usable_kpis, 1, number_of_cells_per_node)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.random')
    def test_reduce_number_of_kpis_continues_on_false_condition(self, mock_random):
        mock_random.choice.side_effect = ['mock', 'RadioNode', u'test kpi']
        usable_kpis = {'RNC': [], 'ERBS': [], 'RadioNode': [u'test kpi']}
        number_of_cells_per_node = {'ERBS': {'number_of_cells': 1000}, 'RNC': {'number_of_cells': 1000},
                                    'RadioNode': {'number_of_cells': 1000}}
        self.flow.reduce_number_of_kpis(usable_kpis, 1000, number_of_cells_per_node)

    def test_get_number_of_custom_kpis_to_create__no_instances_needed(self):
        ret = self.flow.get_number_of_custom_kpis_to_create(300000, Mock(), 0)
        self.assertTrue(ret == {'RNC': 0, 'ERBS': 0, 'RadioNode': 0})

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.random')
    def test_get_number_of_custom_kpis_to_create_success(self, mock_random):
        mock_random.choice.return_value = 'RadioNode'
        kpi_dict = {'RadioNode': {'number_of_cells': 300, 'number_of_nodes': 300},
                    'ERBS': {'number_of_cells': 300, 'number_of_nodes': 300}}
        ret = self.flow.get_number_of_custom_kpis_to_create(200000, kpi_dict, self.flow.NUMBER_OF_INSTANCES_REQUIRED)
        self.assertTrue(ret == {'RNC': 0, 'ERBS': 0, 'RadioNode': 50})

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.random')
    def test_get_number_of_custom_kpis_to_create_no_cells(self, mock_random):
        mock_random.choice.return_value = 'RNC'
        kpi_dict = {'RadioNode': {'number_of_cells': 0, 'number_of_nodes': 300},
                    'ERBS': {'number_of_cells': 300, 'number_of_nodes': 300},
                    'RNC': {'number_of_cells': 300, 'number_of_nodes': 300}}
        ret = self.flow.get_number_of_custom_kpis_to_create(200000, kpi_dict, self.flow.NUMBER_OF_INSTANCES_REQUIRED)
        self.assertTrue(ret == {'RNC': 50, 'ERBS': 0, 'RadioNode': 0})

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    def test_get_default_kpis_throws_an_exception(self, mock_kpi, mock_add_error):
        mock_kpi.get_all_kpi_names.side_effect = Exception()

        self.flow.get_default_kpis(Mock())
        self.assertTrue(mock_kpi.get_all_kpi_names.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.check_is_kpi_usable_and_assign_to_node_type')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_default_kpis')
    def test_get_usable_kpis_http_error(self, mock_get_default_kpis, mock_check_usable, mock_add_error):
        mock_get_default_kpis.return_value = ['kpi1']
        mock_check_usable.side_effect = HTTPError()
        self.flow.get_usable_kpis(Mock())

        self.assertTrue(mock_add_error.called)

    def test_get_number_nodes_and_cells_for_given_node_type_raises_exception_with_greater_batch_size(self):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = None
        mock_user.enm_execute.return_value = mock_response
        nodes_verified_on_enm = [self.mock_node for _ in range(101)]

        with self.assertRaises(NoOuputFromScriptEngineResponseError):
            self.flow.get_number_of_cells_for_given_node_type(mock_user, 'ERBS', nodes_verified_on_enm)

    def test_get_number_nodes_and_cells_for_given_node_type_raises_exception(self):
        mock_user = Mock()
        mock_response = Mock()
        mock_response.get_output.return_value = None
        mock_user.enm_execute.return_value = mock_response
        nodes_verified_on_enm = [self.mock_node]

        with self.assertRaises(NoOuputFromScriptEngineResponseError):
            self.flow.get_number_of_cells_for_given_node_type(mock_user, 'ERBS', nodes_verified_on_enm)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_default_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.check_is_kpi_usable_and_assign_to_node_type')
    def test_get_usable_kpis(self, mock_check_is_kpi_usable, mock_get_default_kpis):
        mock_get_default_kpis.return_value = ['kpi1', 'kpi2', 'kpi3']

        self.flow.get_usable_kpis(Mock())
        self.assertTrue(mock_check_is_kpi_usable.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi.update')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi.activate')
    def test_create_and_activate_cell_level_kpi__if_po_ids_available(self, mock_activate, mock_update, _):
        node_kpi_dict = {'ERBS': ['kpi1'], 'RadioNode': ['kpi1']}
        nodes = [Mock(poid="123", primary_type="ERBS"), Mock(poid=None, primary_typ="RadioNode")]
        self.flow.create_and_activate_cell_level_kpi(Mock(), nodes, node_kpi_dict)
        self.assertEqual(1, mock_activate.call_count)
        self.assertEqual(1, mock_update.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_and_activate_node_level_kpi')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    def test_execute_flow_nhm_01_raises_exception(self, mock_nhm_kpi, mock_create_activate):
        mock_create_activate.side_effect = Exception()
        nodes_verified_on_enm = [self.mock_node]

        self.flow.execute_flow_nhm_01(Mock(), nodes_verified_on_enm)
        self.assertTrue(mock_nhm_kpi.get_counters_specified_by_nhm.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    def test_execute_flow_nhm_01_fails_no_nodes(self, mock_nhm_kpi):

        self.flow.execute_flow_nhm_01(Mock(), [])
        self.assertFalse(mock_nhm_kpi.get_counters_specified_by_nhm.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.'
           'create_and_activate_user_created_cell_level_kpi')
    def test_execute_flow_nhm_02_raises_exception(self, mock_create_activate, mock_log):
        mock_create_activate.side_effect = Exception()
        self.flow.execute_flow_nhm_02(Mock(), [self.mock_node], self.flow.custom_kpis_to_create, self.usable_kpis)

        self.assertTrue(mock_log.logger.info.called)

    def test_check_output_for_num_cells_is_successful(self):
        output = [u'', u'150 instance(s)']
        self.assertEqual(self.flow.check_output_for_num_cells(output), 150)

    def test_check_output_for_num_cells_if_instances_not_in_output(self):
        output = [u'', u'message']
        with self.assertRaises(ScriptEngineResponseValidationError):
            self.flow.check_output_for_num_cells(output)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.log')
    def test_log_calculation_succes(self, mock_log):
        self.flow.log_calculation(5, kpi_overhead=5, reminder=5)

        self.assertTrue(mock_log.logger.info.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.NhmKpi')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_nodes_list_by_attribute')
    @patch("enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.state", new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_active_profile_names')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102._clean_system_nhm_02')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102._clean_system_nhm_01')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_multi_primary_type_router_nodes')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.get_nhm_nodes')
    def test_nhm_01_02_excute_transport_flow(self, mock_get_nodes, mock_create_router, mock_clean_nhm_01,
                                             mock_clean_nhm_02, *_):
        self.flow.NUM_NODES = {'Router6675': -1}
        self.flow.TRANSPORT_SETUP = True
        mock_node = Mock()
        mock_node.primary_type = "Router6675"
        mock_get_nodes.return_value = [mock_node]
        self.flow.execute_flow()
        self.assertTrue(mock_clean_nhm_01.called)
        self.assertTrue(mock_clean_nhm_02.called)
        self.assertEqual(1, mock_create_router.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.math')
    def test_get_number_of_router_kpis_to_create_number_of_kpi_less_than_required(self, mock_math, mock_log):
        mock_math.ceil.return_value = 1
        self.flow.get_number_of_router_kpis_to_create(5)

        self.assertFalse(mock_log.logger.info.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.log')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.math')
    def test_get_number_of_router_kpis_to_create_number_of_kpi_greater_than_required(self, mock_math, mock_log):
        mock_math.ceil.return_value = 6
        self.flow.MAX_NUMBER_OF_CUSTOM_KPIS = 5
        self.flow.get_number_of_router_kpis_to_create(5)
        self.assertEqual(1, mock_log.logger.info.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.track_kpi_creation')
    @patch('enmutils_int.lib.nhm.NhmKpi.get_counters_specified_by_nhm', return_value=["counter"])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_number_of_router_kpis_to_create',
           return_value=1)
    @patch('enmutils_int.lib.nhm.NhmKpi.create')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.add_error_as_exception')
    @patch('enmutils_int.lib.nhm.NhmKpi.activate')
    def test_create_router_kpis__success(self, mock_activate, mock_add_error_as_exception, *_):
        self.flow.nodes_verified_on_enm = []
        self.flow.kpi_name = 'KPI_TEST'
        self.flow.create_router_kpis(Mock(), [Mock(), Mock()])
        self.assertEqual(0, mock_add_error_as_exception.call_count)
        self.assertEqual(1, mock_activate.call_count)

    @patch('enmutils_int.lib.nhm.NhmKpi.get_counters_specified_by_nhm', return_value=["counter"])
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_number_of_router_kpis_to_create',
           return_value=2)
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.add_error_as_exception')
    @patch('enmutils_int.lib.nhm.NhmKpi.create')
    def test_create_router_kpis__adds_exception(self, mock_create, mock_add_error_as_exception, *_):
        self.flow.nodes_verified_on_enm = []
        self.flow.kpi_name = 'KPI_TEST'
        mock_create.side_effect = Exception
        self.flow.create_router_kpis(Mock(), [Mock(), Mock()])
        self.assertEqual(2, mock_add_error_as_exception.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.create_router_kpis')
    def test_create_multi_primary_type_router_nodes__creates_kpi_by_primary_type(self, mock_create_router_kpis):
        user = Mock()
        node, node1 = Mock(), Mock()
        node.primary_type, node1.primary_type = "Router6672", "Router6675"
        nodes = [node, node1]
        self.flow.create_multi_primary_type_router_nodes(user, nodes)
        self.assertEqual(2, mock_create_router_kpis.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_number_of_cells_for_given_node_type')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_profile_node_types')
    def test_get_node_cell_count_dict__exception(self, mock_get_profile_node_types, mock_get_nodes_cells, mock_add_error):
        mock_get_profile_node_types.return_value = ['ERBS', 'RadioNode', 'RNC']
        mock_get_nodes_cells.return_value = Exception()
        self.flow.get_node_cell_count_dict(Mock(), [Mock(), Mock()])
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.log_calculation')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.reduce_number_of_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_usable_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_max_number_of_node_level_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.'
           'calculate_the_total_number_of_kpi_instances_avaiable')
    def test_calculate_expected_kpi_instances__if_more_kpis(self, mock_caculate_number, mock_get_node_kpis,
                                                            mock_get_usable_kpis, mock_reduce_kpis,
                                                            mock_log_calculation):
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = ["100 instance(s)"]
        mock_caculate_number.return_value = self.flow.NUMBER_OF_INSTANCES_REQUIRED
        self.flow.calculate_expected_kpi_instances(Mock(), [Mock()], self.flow.NUMBER_OF_INSTANCES_REQUIRED)
        self.assertTrue(mock_get_node_kpis.called)
        self.assertTrue(mock_get_usable_kpis.called)
        self.assertTrue(mock_caculate_number.called)
        self.assertTrue(mock_reduce_kpis.called)
        self.assertTrue(mock_log_calculation.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.log_calculation')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_number_of_custom_kpis_to_create')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_usable_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.get_max_number_of_node_level_kpis')
    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.Nhm0102.'
           'calculate_the_total_number_of_kpi_instances_avaiable')
    def test_calculate_expected_kpi_instances__if_less_kpis(self, mock_caculate_number, mock_get_node_kpis,
                                                            mock_get_usable_kpis, mock_custom_kpis,
                                                            mock_log_calculation):
        mock_enm_response = Mock()
        mock_enm_response.get_output.return_value = ["100 instance(s)"]
        mock_caculate_number.return_value = self.flow.MAX_NUMBER_OF_CUSTOM_KPIS
        self.flow.calculate_expected_kpi_instances(Mock(), [Mock()], self.flow.NUMBER_OF_INSTANCES_REQUIRED)
        self.assertTrue(mock_get_node_kpis.called)
        self.assertTrue(mock_get_usable_kpis.called)
        self.assertTrue(mock_caculate_number.called)
        self.assertTrue(mock_custom_kpis.called)
        self.assertTrue(mock_log_calculation.called)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time.sleep', return_value=0)
    def test_track_kpi_creation__success(self, mock_sleep):
        user = Mock()
        kpi_name = "KPI"
        response = Mock(_content="id", status_code=200)
        user.get.side_effect = [Exception("Error"), response]
        self.flow.track_kpi_creation(response, user, kpi_name)
        self.assertEqual(1, mock_sleep.call_count)

    @patch('enmutils_int.lib.profile_flows.nhm_flows.nhm_01_02_flow.time.sleep', return_value=0)
    def test_track_kpi_creation__polls(self, mock_sleep):
        user = Mock()
        kpi_name = "KPI"
        response = Mock(_content="id", status_code=202)
        user.get.return_value = response
        self.flow.track_kpi_creation(response, user, kpi_name)
        self.assertEqual(3, mock_sleep.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
