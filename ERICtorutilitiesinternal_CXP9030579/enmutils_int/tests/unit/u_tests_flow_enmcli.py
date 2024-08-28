#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock, mock_open, call

from testslib import unit_test_utils
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow import (EnmCli01Flow, EnmCli02Flow, EnmCli05Flow,
                                                                     EnmCli03Flow, ScriptingTaskset, SSHException,
                                                                     EnmCli08Flow)


class EnmCli01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = EnmCli01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.get_nodes_list_by_attribute',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_create_and_execute_threads, mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_network_sync_status')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.'
           'list_objects_in_network_that_match_specific_criteria')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_bfd')
    def test_taskset_calls_bfd(self, mock_get_bfd, *_):
        self.flow.NODES = [Mock(node_id='node123', lte_cell_type=None)]
        self.flow.task_set(self.user, self.flow)
        self.assertTrue(mock_get_bfd.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice', return_value=1)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_network_sync_status')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.'
           'list_objects_in_network_that_match_specific_criteria')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cells_zzztemporary34_csirsperiodicity')
    def test_taskset__get_cells_zzztemporary34_csirsperiodicity_4g(self, mock_get_cells_zzztemporary34_csirsperiodicity, *_):
        self.flow.NODE_TYPE = 'GNodeB'
        self.flow.NODES = [Mock(node_id='node123', lte_cell_type=None)]
        self.flow.task_set(self.user, self.flow)
        mock_get_cells_zzztemporary34_csirsperiodicity.assert_called_once_with(self.user, 'node123', 'GNodeB', 'NRCellDU')

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice', return_value=1)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_network_sync_status')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.'
           'list_objects_in_network_that_match_specific_criteria')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cells_zzztemporary34_csirsperiodicity')
    def test_taskset__get_cells_zzztemporary34_csirsperiodicity_5g_fdd(self, mock_get_cells_zzztemporary34_csirsperiodicity, *_):
        self.flow.NODE_TYPE = 'ENodeB'
        self.flow.NODES = [Mock(node_id='node123', lte_cell_type='FDD')]
        self.flow.task_set(self.user, self.flow)
        mock_get_cells_zzztemporary34_csirsperiodicity.assert_called_once_with(self.user, 'node123', 'ENodeB', 'EUtranCellFDD')

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice', return_value=1)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_network_sync_status')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.'
           'list_objects_in_network_that_match_specific_criteria')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cells_zzztemporary34_csirsperiodicity')
    def test_taskset__get_cells_zzztemporary34_csirsperiodicity_5g_tdd(self, mock_get_cells_zzztemporary34_csirsperiodicity, *_):
        self.flow.NODE_TYPE = 'ENodeB'
        self.flow.NODES = [Mock(node_id='node123', lte_cell_type='TDD')]
        self.flow.task_set(self.user, self.flow)
        mock_get_cells_zzztemporary34_csirsperiodicity.assert_called_once_with(self.user, 'node123', 'ENodeB', 'EUtranCellTDD')

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice', return_value=1)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_network_sync_status')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.'
           'list_objects_in_network_that_match_specific_criteria')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cells_zzztemporary34_csirsperiodicity', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli01Flow.add_error_as_exception')
    def test_taskset_catches_exception(self, mock_error, *_):
        self.flow.NODES = [Mock()]
        self.flow.task_set(self.user, self.flow)
        self.assertEqual(mock_error.call_count, 1)


class EnmCli02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = EnmCli02Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.SCHEDULE_SLEEP = 15
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.create_profile_users')
    def test_execute_flow__successful(self, mock_create_profile_users, mock_create_and_execute_threads, mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.create_profile_users')
    def test_execute_flow__calls_exchange_nodes(self, mock_create_profile_users, mock_create_and_execute_threads,
                                                mock_sleep, mock_exchange, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertEqual(mock_exchange.call_count, 1)
        self.assertTrue(mock_sleep.called)

    def test_get_new_attribute_values(self):
        attribute = {"Attr": "false", "Attr1": "true"}
        attributes = self.flow.get_new_attribute_values(attribute)
        self.assertEqual(attributes.get("Attr"), "true")
        self.assertEqual(attributes.get("Attr1"), "false")

    def test_get_new_attribute_values_ignores_unmatched(self):
        attribute = {"Attr": 0}
        attributes = self.flow.get_new_attribute_values(attribute)
        self.assertTrue(len(attributes) is 0)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.get_new_attribute_values')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_help')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.set_cell_attributes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cell_relations')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cell_attributes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_administrator_state')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_node_cells', return_value=['cell1-1'])
    def test_task_set__lte_node_fdd(self, mock_get_node_cells, mock_admin_state, mock_get_cell_attributes, *_):
        worker = (Mock(), Mock(node_id='LTE40dg2ERBS00001', lte_cell_type='FDD'))

        self.flow.task_set(worker, self.flow)
        mock_get_node_cells.assert_called_with(worker[0], worker[1], cell_type='EUtranCellFDD')
        mock_admin_state.assert_called_with(worker[0], worker[1], cell_type='EUtranCellFDD')
        mock_get_cell_attributes.assert_called_with(worker[0], worker[1], 'cell1-1',
                                                    ['cfraEnable', 'acBarringForCsfbPresent', 'acBarringForMoSignallingPresent'],
                                                    cell_type='EUtranCellFDD')

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.get_new_attribute_values')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_help')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.set_cell_attributes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cell_relations')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cell_attributes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_administrator_state')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_node_cells', return_value=['cell1-1'])
    def test_task_set__lte_node_tdd(self, mock_get_node_cells, mock_admin_state, mock_get_cell_attributes, *_):
        worker = (Mock(), Mock(node_id='LTE40dg2ERBS00001', lte_cell_type='TDD'))

        self.flow.task_set(worker, self.flow)
        mock_get_node_cells.assert_called_with(worker[0], worker[1], cell_type='EUtranCellTDD')
        mock_admin_state.assert_called_with(worker[0], worker[1], cell_type='EUtranCellTDD')
        mock_get_cell_attributes.assert_called_with(worker[0], worker[1], 'cell1-1',
                                                    ['cfraEnable', 'acBarringForCsfbPresent',
                                                     'acBarringForMoSignallingPresent'], cell_type='EUtranCellTDD')

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.get_new_attribute_values')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_help')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.set_cell_attributes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cell_relations')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_cell_attributes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_administrator_state')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_node_cells', return_value=['cell1-1'])
    def test_task_set__5g_node(self, mock_get_node_cells, mock_admin_state, mock_get_cell_attributes, *_):
        worker = (Mock(), Mock(node_id='NR01gNodeBRadio00015', lte_cell_type=None))

        self.flow.task_set(worker, self.flow)
        mock_get_node_cells.assert_called_with(worker[0], worker[1], cell_type='NRCellCU')
        mock_admin_state.assert_called_with(worker[0], worker[1], cell_type='NRCellDU')
        mock_get_cell_attributes.assert_called_with(worker[0], worker[1], 'cell1-1',
                                                    ['transmitSib2', 'transmitSib4', 'transmitSib5'],
                                                    cell_type='NRCellCU')

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_node_cells', side_effect=Exception('Error'))
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli02Flow.add_error_as_exception')
    def tests_task_set__error_caught(self, mock_add_error, *_):
        worker = (Mock(), Mock(node_id='NR01gNodeBRadio00015', lte_cell_type=None))
        self.flow.task_set(worker, self.flow)

        self.assertEqual(mock_add_error.call_count, 1)


class EnmCli03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = EnmCli03Flow()
        self.flow.IS_CLOUD_NATIVE = False
        self.flow.NUM_USERS = 10
        self.flow.USER_ROLES = ["Admin"]
        self.exception = Exception("Some Exception")
        self.flow.enmcli_commands_list = {'alarm': ['alarm get {node_id} --critical --warning'],
                                          'cmedit_basic': {'eNodeB': ['cmedit get {node_id} MeContext'],
                                                           'gNodeB': ['cmedit get {ten_node_id} NRCellCU.*']},
                                          'cmedit_standard': {'eNodeB': ['cmedit get {ten_node_id} MeContext'],
                                                              'gNodeB': ['cmedit get {ten_node_id} NRCellCU.*']},
                                          'cmedit_advanced': {
                                              'eNodeB': ['cmedit get * ManagedElement -neType=SGSN-MME'],
                                              'gNodeB': ['cmedit get {ninetynine_node_id} RetSubUnit.(maxTilt>-1500, '
                                                         'iuantAntennaOperatingBand==-1000)']},
                                          'secadm': ['secadm cert get -ct OAM -n {node_id}']}
        self.flow.total_commands_sec = 1000
        self.flow.percentage_cm_bas = self.flow.percentage_cm_std = self.flow.percentage_cm_adv = 20
        self.flow.percentage_alarm = self.flow.percentage_secadm = 20

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_nodes_list_by_attribute',
           return_value=[Mock()] * 10)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.load_balance',
           return_value=(1, 2, 3, 4))
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_scripting_iterator',
           return_value=[Mock()] * 10)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips',
           return_value="scp1")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.create_commands_list')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.delete_user_sessions')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._deploy_execution_file')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_create_and_execute_threads, mock_sleep,
                          mock_deploy_execution_file, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_deploy_execution_file.side_effect = [self.exception, None]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)
        self.assertEqual(1, len(mock_create_and_execute_threads.call_args[0]))
        self.assertEqual(2, len(mock_create_and_execute_threads.call_args[1]))
        self.assertEqual(1, len(mock_create_and_execute_threads.call_args[1]['args']))

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_nodes_list_by_attribute',
           return_value=[Mock()] * 10)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.load_balance',
           return_value=(1, 2, 3, 4))
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_scripting_iterator',
           return_value=[Mock()] * 10)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips',
           return_value="scp1")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.create_commands_list')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.delete_user_sessions')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._deploy_execution_file')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.'
           'create_common_directory_in_scripting_cluster')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.create_profile_users')
    def test_execute_flow__cloud_native(self, mock_create_profile_users, mock_create_and_execute_threads,
                                        mock_sleep, mock_create_dir, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_dir.called)
        mock_create_dir.side_effect = [self.exception, None]
        self.assertTrue(mock_sleep.called)
        self.assertEqual(1, len(mock_create_and_execute_threads.call_args[0]))
        self.assertEqual(2, len(mock_create_and_execute_threads.call_args[1]))
        self.assertEqual(1, len(mock_create_and_execute_threads.call_args[1]['args']))

    def test_maintain_iter_value(self):
        iterator = self.flow.maintain_iter_value(0, 1)
        self.assertEqual(iterator, 0)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    def test_create_common_directory_in_scripting_cluster__directory_exists_or_created(self, mock_run_cmd, mock_host):
        mock_run_cmd.return_value = Mock(rc=0)
        mock_host.return_value = "scp1"
        self.flow.create_common_directory_in_scripting_cluster([self.user])
        self.assertEqual(mock_run_cmd.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    def test_create_common_directory_in_scripting_cluster__raises_environ_error(self, mock_run_cmd, mock_host):
        mock_run_cmd.return_value = Mock(rc=1)
        mock_host.return_value = "scp1"
        self.assertRaises(EnvironError, self.flow.create_common_directory_in_scripting_cluster, [self.user])
        self.assertEqual(mock_run_cmd.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd', side_effect=Exception)
    def test_create_common_directory_in_scripting_cluster__raises_enm_application_error(self, mock_run_cmd, mock_host, _):
        mock_run_cmd.return_value = Mock(rc=1)
        mock_host.return_value = "scp1"
        self.assertRaises(EnmApplicationError, self.flow.create_common_directory_in_scripting_cluster, [self.user])
        self.assertEqual(mock_run_cmd.call_count, 1)

    # create_commands_list test cases
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.ScriptingTaskset')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_enmcli_command_based_on_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.info')
    def test_create_commands_list__if_node_type_5g(self, mock_info, mock_get_enmcli_command, mock_scripting_taskset, *_):
        self.flow.NODE_TYPE = 'GNodeB'
        mock_node = Mock(node_id='node123', lte_cell_type=None)
        mocks = [Mock()] * 10
        users = (mocks, mocks)
        command_users = (1, 2, 3, 4)
        mock_get_enmcli_command.return_value = ("cmedit get {ten_node_id} NRCellDU.(administrativeState, "
                                                "operationalState) -t")
        commands_string = ';;'.join([mock_get_enmcli_command.return_value] * 6)
        self.assertIsNotNone(self.flow.create_commands_list(users, 6, command_users, [mock_node], 0))
        mock_scripting_taskset.assert_called_with(cell_type=mock_node.lte_cell_type, scripting_hostname=users[0][0],
                                                  sleep=27, user=users[0][0], command=commands_string,
                                                  nodes=[mock_node])
        self.assertTrue(mock_get_enmcli_command.called)
        self.assertTrue(mock_info.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.ScriptingTaskset')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_enmcli_command_based_on_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.info')
    def test_create_commands_list__if_node_type_4g_fdd(self, mock_info, mock_get_enmcli_command,
                                                       mock_scripting_taskset, *_):
        self.flow.NODE_TYPE = 'ENodeB'
        mock_node = Mock(node_id='LTE0213ERBS0123', lte_cell_type='FDD')
        mocks = [Mock()] * 10
        users = (mocks, mocks)
        command_users = (1, 2, 3, 4)
        mock_get_enmcli_command.return_value = "cmedit get {ninetynine_node_id} {cell_type}.(altitude>0, tac==1)"
        commands_string = ';;'.join([mock_get_enmcli_command.return_value] * 6)
        self.assertIsNotNone(self.flow.create_commands_list(users, 6, command_users, [mock_node], 0))
        self.assertTrue(mock_info.called)
        mock_scripting_taskset.assert_called_with(cell_type="EUtranCellFDD", scripting_hostname=users[0][0],
                                                  sleep=27, user=users[0][0], command=commands_string,
                                                  nodes=[mock_node])
        self.assertTrue(mock_get_enmcli_command.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.ScriptingTaskset')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_enmcli_command_based_on_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.info')
    def test_create_commands_list__if_node_type_4g_tdd(self, mock_info, mock_get_enmcli_command,
                                                       mock_scripting_taskset, *_):
        self.flow.NODE_TYPE = 'ENodeB'
        mock_node = Mock(node_id='LTE0213ERBS0123', lte_cell_type='TDD')
        mocks = [Mock()] * 10
        users = (mocks, mocks)
        command_users = (1, 2, 3, 4)
        mock_get_enmcli_command.return_value = "cmedit get {ten_node_id} MeContext"
        commands_string = ';;'.join([mock_get_enmcli_command.return_value] * 6)
        self.assertIsNotNone(self.flow.create_commands_list(users, 6, command_users, [mock_node], 0))
        self.assertTrue(mock_info.called)
        mock_scripting_taskset.assert_called_with(cell_type="EUtranCellTDD", scripting_hostname=users[0][0],
                                                  sleep=27, user=users[0][0], command=commands_string,
                                                  nodes=[mock_node])
        self.assertTrue(mock_get_enmcli_command.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.ScriptingTaskset')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_enmcli_command_based_on_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.info')
    def test_create_commands_list___handles_empty_user_list(self, mock_info, mock_get_enmcli_command,
                                                            mock_scripting_taskset, *_):
        mock_node = Mock(node_id='LTE0213ERBS0123', lte_cell_type='FDD')
        users = ([], [])
        command_users = (1, 2, 3, 4)
        mock_get_enmcli_command.return_value = "cmedit get {ten_node_id} MeContext"
        self.assertEqual(0, len(self.flow.create_commands_list(users, 10, command_users, [mock_node], 0)))
        self.assertFalse(mock_get_enmcli_command.called)
        self.assertFalse(mock_scripting_taskset.called)
        self.assertFalse(mock_info.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.random.choice')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.ScriptingTaskset')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.get_enmcli_command_based_on_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.info')
    def test_create_commands_list__handles_empty_scripting_user_list(self, mock_info, mock_get_enmcli_command,
                                                                     mock_scripting_taskset, *_):
        mock_node = Mock(node_id='LTE0213ERBS0123', lte_cell_type='FDD')
        mocks = [Mock()] * 10
        users = (mocks, [])
        command_users = (1, 2, 3, 4)
        mock_get_enmcli_command.return_value = "cmedit get {ten_node_id} MeContext"
        self.assertEqual(0, len(self.flow.create_commands_list(users, 10, command_users, [mock_node], 0)))
        self.assertTrue(mock_get_enmcli_command.called)
        self.assertFalse(mock_scripting_taskset.called)
        self.assertTrue(mock_info.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_specific_scripting_iterator')
    def test_get_scripting_iterator(self, mock_get_specific_scripting_iterator):
        mock_get_specific_scripting_iterator.return_value = Mock()
        self.assertIsNotNone(self.flow.get_scripting_iterator([Mock()]))

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_specific_scripting_iterator')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_get_scripting_iterator_adds_error(self, mock_add_error, mock_get_specific_scripting_iterator):
        mock_get_specific_scripting_iterator.side_effect = self.exception
        self.flow.get_scripting_iterator([Mock()])
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_workload_admin_user', return_value=Mock())
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.delete_left_over_sessions')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_delete_user_sessions_adds_error_on_failure(self, mock_add_error, mock_delete_left_over_sessions, _):
        mock_delete_left_over_sessions.side_effect = [self.exception, None]
        self.flow.delete_user_sessions([Mock(), Mock()])
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_local_cmd')
    def test_make_file_executable_raises_exception(self, mock_run_local_cmd):
        response = Mock()
        response.rc = 1
        response.stdout = "Error"
        mock_run_local_cmd.return_value = response
        self.assertRaises(EnvironError, self.flow._make_file_executable)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_local_cmd')
    def test_make_file_executable(self, mock_run_local_cmd):
        response = Mock()
        response.rc = 0
        response.stdout = "Success"
        mock_run_local_cmd.return_value = response
        self.flow._make_file_executable()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_local_cmd')
    def test_copy_to_emp_raises_exception(self, mock_run_local_cmd):
        response = Mock()
        response.rc = 1
        response.stdout = "Error"
        mock_run_local_cmd.return_value = response
        self.assertRaises(EnvironError, self.flow._copy_to_emp, "1234", "command")

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_local_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.debug')
    def test_copy_to_emp(self, mock_debug, mock_run_local_cmd):
        response = Mock()
        response.rc = 0
        response.stdout = "Success"
        mock_run_local_cmd.return_value = response
        self.flow._copy_to_emp("1234", "command")
        self.assertTrue(mock_debug.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_cmd_on_vm')
    def test_copy_to_cloud_scripting_clusters_raises_exception(self, mock_run_cmd_on_vm):
        response = Mock()
        response.rc = 1
        response.stdout = "Error"
        mock_run_cmd_on_vm.return_value = response
        self.assertRaises(EnvironError, self.flow._copy_to_cloud_scripting_clusters, "1234", "command", "scp")

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_cmd_on_vm')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.debug')
    def test_copy_to_cloud_scripting_clusters(self, mock_debug, mock_run_cmd_on_vm):
        response = Mock()
        response.rc = 0
        response.stdout = "Success"
        mock_run_cmd_on_vm.return_value = response
        self.flow._copy_to_cloud_scripting_clusters("1234", "command", "scp")
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_local_cmd')
    def test_copy_to_scripting_clusters_raises_exception(self, mock_run_local_cmd):
        response = Mock()
        response.rc = 1
        response.stdout = "Error"
        mock_run_local_cmd.return_value = response
        self.assertRaises(EnvironError, self.flow._copy_to_scripting_clusters, "command", "scp")

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.enm_deployment.get_pod_hostnames_in_cloud_native',
           return_value=["general-scripting1", "general-scripting2"])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.copy_file_between_wlvm_and_cloud_native_pod')
    def test_copy_to_scripting_clusters__if_cloud_native_raises_exception(self, mock_copy, _):
        self.flow.IS_CLOUD_NATIVE = True
        mock_copy.side_effect = [Mock(rc=1), Mock(rc=1)]
        self.assertRaises(EnvironError, self.flow._copy_to_scripting_clusters, "command", "scp")
        self.assertTrue(mock_copy.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_local_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.debug')
    def test_copy_to_scripting_clusters(self, mock_debug, mock_run_local_cmd):
        response = Mock()
        response.rc = 0
        response.stdout = "Success"
        mock_run_local_cmd.return_value = response
        self.flow._copy_to_scripting_clusters("command", "scp")
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.enm_deployment.get_pod_hostnames_in_cloud_native',
           return_value=["general-scripting"])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.copy_file_between_wlvm_and_cloud_native_pod')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.debug')
    def test_copy_to_scripting_clusters__if_cloud_native(self, mock_debug, mock_copy, *_):
        response = Mock()
        response.rc = 0
        response.stdout = "Success"
        mock_copy.return_value = response
        self.flow.IS_CLOUD_NATIVE = True
        self.flow._copy_to_scripting_clusters("command", "scp")
        self.assertTrue(mock_copy.called)
        self.assertEqual(mock_debug.call_count, 2)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_emp', return_value="1234")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.enm_deployment.get_cloud_members_ip_address',
           return_value="scp1")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_cloud_scripting_clusters')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_emp')
    def test_deploy_execution_file(self, mock_copy_to_emp, mock_copy_scp, mock_debug, *_):
        mock_copy_to_emp.return_value = None
        mock_copy_scp.side_effect = None
        self.flow._deploy_execution_file()
        self.assertFalse(mock_debug.called)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_emp', return_value="1234")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_emp')
    def test_deploy_execution_script_raises_exception_cloud_emp_failure(self, mock_copy_to_emp, *_):
        mock_copy_to_emp.side_effect = self.exception
        self.assertRaises(Exception, self.flow._deploy_execution_file)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_emp', return_value="1234")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.enm_deployment.get_cloud_members_ip_address',
           return_value="scp1")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_cloud_scripting_clusters')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_emp')
    def test_deploy_execution_script_logs_error_cloud_scp_failure(self, mock_copy_to_emp, mock_copy_scp, mock_add_error,
                                                                  *_):
        mock_copy_to_emp.return_value = None
        mock_copy_scp.side_effect = self.exception
        self.flow._deploy_execution_file()
        self.assertTrue(mock_add_error.called)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_emp', return_value=False)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips',
           return_value="scp1")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_scripting_clusters')
    def test_deploy_execution_script_logs_error_physical_scp_failure(self, mock_copy_to_scripting_clusters,
                                                                     mock_add_error, *_):
        mock_copy_to_scripting_clusters.side_effect = self.exception
        self.flow._deploy_execution_file()
        self.assertTrue(mock_add_error.called)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.is_emp', return_value=False)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.deploymentinfomanager_adaptor.get_list_of_scripting_service_ips',
           return_value="scp1")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow._copy_to_scripting_clusters')
    def test_deploy_execution_script_on_physical_scp(self, mock_copy_to_scripting_clusters, *_):
        mock_copy_to_scripting_clusters.return_value = None
        self.flow._deploy_execution_file()
        self.assertTrue(mock_copy_to_scripting_clusters.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_task_set__adds_error_on_exception(self, mock_add_errror, mock_run_cmd_on_vm, _):
        mock_run_cmd_on_vm.side_effect = self.exception
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_add_errror.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.Command')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_task_set__if_cloud_native_adds_error_on_exception(self, mock_add_errror, mock_run_cmd, *_):
        self.flow.IS_CLOUD_NATIVE = True
        mock_run_cmd.side_effect = self.exception
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_add_errror.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.Command')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_task_set__adds_error_on_return_code(self, mock_add_errror, mock_run_cmd_on_vm, *_):
        response = Mock()
        response.rc = 1
        response.stdout = "Error"
        mock_run_cmd_on_vm.return_value = response
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_add_errror.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.Command')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_task_set__if_cloud_native_adds_error_on_return_code(self, mock_add_errror, mock_run_cmd, *_):
        response = Mock()
        response.rc = 1
        response.stdout = "Error"
        mock_run_cmd.return_value = response
        self.flow.IS_CLOUD_NATIVE = True
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_add_errror.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_task_set__adds_environ_error_if_ssh_exception(self, mock_add_error, mock_run_cmd_on_vm, _):
        mock_run_cmd_on_vm.side_effect = SSHException("Error message")
        self.flow.task_set(Mock(), self.flow)
        self.assertTrue(mock_add_error.called)
        self.assertIsInstance(mock_add_error.call_args[0][0], EnvironError)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.run_remote_cmd')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli03Flow.add_error_as_exception')
    def test_task_set(self, mock_add_errror, mock_run_cmd_on_vm, _):
        response = Mock()
        response.rc = 0
        response.stdout = "Success"
        mock_run_cmd_on_vm.return_value = response
        self.flow.task_set(Mock(), self.flow)
        self.assertFalse(mock_add_errror.called)

    def test_load_balance_returns_correct_load(self):
        expected = 22, 68, 90, 95
        result = self.flow.load_balance(100, 100, 22.5, 45, 22.5, 5, 5)
        self.assertEqual(expected, result)

    # get_enmcli_command_based_on_users test cases

    def test_get_enmcli_command_based_on_users__if_node_type_enodeb_and_returns_cmedit_basic_cmd(self):
        node_type = "eNodeB"
        command = self.flow.get_enmcli_command_based_on_users(0, 1, 2, 3, 4, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['cmedit_basic'][node_type][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_enodeb_and_returns_cmedit_standard_cmd(self):
        node_type = "eNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 2, 3, 4, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['cmedit_standard'][node_type][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_enodeb_and_returns_cmedit_advanced_cmd(self, *_):
        node_type = "eNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 0, 2, 4, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['cmedit_advanced'][node_type][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_enodeb_alarm_cmd(self, *_):
        node_type = "eNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 0, 0, 2, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['alarm'][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_enodeb_secadm_cmd(self, *_):
        node_type = "eNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 0, 0, 0, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['secadm'][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_gnodeb_and_returns_cmedit_basic_cmd(self):
        node_type = "gNodeB"
        command = self.flow.get_enmcli_command_based_on_users(0, 1, 2, 3, 4, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['cmedit_basic'][node_type][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_gnodeb_and_returns_cmedit_standard_cmd(self):
        node_type = "gNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 2, 3, 4, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['cmedit_standard'][node_type][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_gnodeb_and_returns_cmedit_advanced_cmd(self, *_):
        node_type = "gNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 0, 2, 4, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['cmedit_advanced'][node_type][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_gnodeb_alarm_cmd(self, *_):
        node_type = "gNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 0, 0, 2, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['alarm'][0], command)

    def test_get_enmcli_command_based_on_users__if_node_type_gnodeb_secadm_cmd(self, *_):
        node_type = "gNodeB"
        command = self.flow.get_enmcli_command_based_on_users(1, 0, 0, 0, 0, node_type)
        self.assertEqual(self.flow.enmcli_commands_list['secadm'][0], command)


class EnmCli05FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = EnmCli05Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.nodes_list', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_random_string', return_value="abcdef")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.Collection.create')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.add_error_as_exception')
    def test_manage_collection__successful(self, mock_add_error_as_exception, *_):
        self.flow.manage_collection(self.user)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.nodes_list', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_random_string', return_value="abcdef")
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.Collection.create')
    def test_manage_collection__add_error_on_exception(self, mock_create, mock_add_error_as_exception, *_):
        mock_create.side_effect = self.exception
        self.flow.manage_collection(self.user)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_collection')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.manage_collection')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.create_profile_users')
    def test_execute_flow_calls_manage_collection_if_no_collection(self, mock_create_profile_users,
                                                                   mock_manage_collection, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_manage_collection.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_collection')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        collection = Mock()
        collection.id = 1
        self.flow.collection = collection
        self.flow.execute_flow()
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.cm_cli_home')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.get_collection')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli05Flow.create_profile_users')
    def test_execute_flow_add_error_on_exception(self, mock_create_profile_users, mock_get_collection,
                                                 mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_get_collection.side_effect = self.exception
        collection = Mock()
        collection.id = 1
        self.flow.collection = collection
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)


class ScriptingTasksetUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_scripting_task_set_creates_correct_node_patterns(self):
        node = Mock()
        node.node_id = "LTE01ERBS00001"
        node.lte_cell_type = "FDD"
        scripting = ScriptingTaskset(Mock(), "command", "scp", [node], 0, cell_type="EUtranCellFDD")
        self.assertEqual("LTE01ERBS0001*", scripting.ten_node_id)
        self.assertEqual("LTE01ERBS000*", scripting.ninetynine_node_id)
        node.node_id = "LTE01ERBS00111"
        node.lte_cell_type = "FDD"
        scripting = ScriptingTaskset(Mock(), "command", "scp", [node], 0, cell_type="EUtranCellFDD")
        self.assertEqual("LTE01ERBS0011*", scripting.ten_node_id)
        self.assertEqual("LTE01ERBS000*", scripting.ninetynine_node_id)


class EnmCli08FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = [Mock()]
        self.flow = EnmCli08Flow()
        self.flow.NAME = "TEST_FLOW"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Role"]
        self.flow.SLEEP_TIME_BETWEEN_COMMANDS = 0

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.get_nodes_list_by_attribute',
           return_value=[Mock(node_id="Node")])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.get_mo', return_value=None)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.log.logger.debug')
    def test_execute_flow__no_mo(self, mock_debug, *_):
        self.flow.execute_flow()
        mock_debug.assert_called_with("No card=1 MO found on node: [Node]")

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.get_nodes_list_by_attribute',
           return_value=[Mock(node_id="Node")])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.get_mo')
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.execute_command_on_enm_cli',
           side_effect=[None, None, None, Exception("Error")])
    def test_execute_flow__success(self, mock_execute, mock_get_mo, mock_user, *_):
        CREATE_CMD = 'cmedit create MO,mode=1 mode-key=1'
        UPDATE_CMD1 = 'cmedit set MO speed=1000'
        UPDATE_CMD2 = 'cmedit set MO speed=100'
        DELETE_CMD = 'cmedit delete MO,mode=1'
        mock_get_mo.return_value = 'MO'
        mock_user.return_value = self.user
        self.flow.execute_flow()
        self.assertTrue(mock_execute.mock_calls == [call(mock_user.return_value[0], CREATE_CMD),
                                                    call(mock_user.return_value[0], UPDATE_CMD1),
                                                    call(mock_user.return_value[0], UPDATE_CMD2),
                                                    call(mock_user.return_value[0], DELETE_CMD)])

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.execute_command_on_enm_cli')
    def test_get_mo__success(self, mock_execute):
        response = Mock()
        response.get_output.return_value = [u'attr', u'FDN : FDN', u'', u'1 instance(s)']
        mock_execute.return_value = response
        self.assertEqual("FDN", self.flow.get_mo(Mock(), "cmd"))

    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.execute_command_on_enm_cli',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.enmcli_flows.enmcli_flow.EnmCli08Flow.add_error_as_exception')
    def test_get_mo__adds_error(self, mock_add_error, _):
        self.assertEqual(None, self.flow.get_mo(Mock(), "cmd"))
        self.assertEqual(1, mock_add_error.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
