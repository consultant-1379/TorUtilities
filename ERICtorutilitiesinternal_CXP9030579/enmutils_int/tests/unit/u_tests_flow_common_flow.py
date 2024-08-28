#!/usr/bin/env python
from datetime import datetime, timedelta
from mock import patch, Mock, call, PropertyMock, MagicMock
import unittest2

from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.common_flows.common_flow import (PlaceHolderFlow, GenericFlow, FMAlarmFlow,
                                                                     verify_and_generate_ssh_keys,
                                                                     get_supported_data_types_from_fls,
                                                                     get_matched_supported_datatypes_with_configured_datatypes,
                                                                     get_active_postgres_db_hostname, is_enm_on_rack)
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class CommonFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.user.username = "mock"
        self.node = Mock()
        self.node.node_ip = generate_configurable_ip(ipversion=6)
        self.used_node = Mock()
        self.used_node.node_id = "ABC"
        self.unused_node = Mock()
        self.is_cloud_native = True
        self.is_physical = True
        self.DATA_TYPES = ["PM_STATISTICAL", "PM_UETR", "TOPOLOGY_*"]
        self.unused_node.node_id = "EFG"
        self.nodes_list = [Mock(poid="27246", primary_type="RadioNode", node_id="LTE98dg2ERBS00001",
                                profiles=["ASR_L_01"]),
                           Mock(poid="27227", primary_type="ERBS", node_id="netsim_LTE02ERBS00040",
                                profiles=["ASR_L_01"]),
                           Mock(poid="27389", primary_type="ERBS", node_id="netsim_LTE02ERBS00041",
                                profiles=["ASR_L_01"])]
        self.get_network_mo_info_response = {'EUtranCellFDD': [
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00001 - 1',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00001 - 2',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00001 - 3',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00002 - 1',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00002 - 2',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00003,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00003 - 1']}
        self.group_mos_by_node_resp = {'netsim_LTE02ERBS00001': [
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00001 - 1',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00001 - 2',
            u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00001,ManagedElement=1,ENodeBFunction=1,'
            u'EUtranCellFDD = LTE02ERBS00001 - 3'], 'netsim_LTE02ERBS00002': [
                u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,'
                u'EUtranCellFDD = LTE02ERBS00002 - 1',
                u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00002,ManagedElement=1,ENodeBFunction=1,'
                u'EUtranCellFDD = LTE02ERBS00002 - 2'], 'netsim_LTE02ERBS00003': [
                    u'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE02ERBS00003,ManagedElement=1,ENodeBFunction=1,'
                    u'EUtranCellFDD = LTE02ERBS00003 - 1']}

        unit_test_utils.setup()
        self.placeholder = PlaceHolderFlow()
        self.placeholder.NOTE = "Test note"
        self.generic = GenericFlow()
        self.generic.RUN_UNTIL = ["18:00:00"]
        self.fmalarm = FMAlarmFlow()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.error')
    def test_placeholder_logs_note(self, mock_error, *_):
        self.placeholder.execute_flow()
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.error')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_placeholder_adds_error_as_exception(self, mock_add_error, *_):
        self.placeholder.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.ThreadQueue.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.ThreadQueue.execute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.process_thread_queue_errors')
    def test_create_and_execute_threads__with_worker_list(self, mock_process_thread_queue, *_):
        self.generic.task_set([self.placeholder], self.fmalarm)
        self.generic.create_and_execute_threads([self.fmalarm], 1)
        self.assertTrue(mock_process_thread_queue.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    def test_create_and_execute_threads__adds_error_on_empty_worker_list(self, mock_add_error_as_exception):
        self.generic.create_and_execute_threads([], 1)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr.exchange_nodes')
    def test_exchange_nodes__uses_legacy(self, mock_exchange_nodes, *_):
        self.generic.exchange_nodes()
        self.assertTrue(mock_exchange_nodes.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.can_service_be_used', return_value=False)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr.exchange_nodes', side_effect=Exception("Exception"))
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    def test_exchange_nodes__adds_error_on_exception(self, mock_add_error_as_exception, *_):
        self.generic.exchange_nodes()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.can_service_be_used', return_value=True)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.exchange_nodes')
    def test_exchange_nodes__uses_service(self, mock_service, *_):
        self.generic.exchange_nodes()
        self.assertEqual(1, mock_service.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.set_up_alarm_text_size_and_problem_distribution")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.map_alarm_rate_with_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.set_up_event_type_and_probable_cause")
    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.setup_alarm_burst")
    def test_configure_fm_alarm_burst_is_successful(self, mock_setup_alarm_burst, mock_add_error_as_exception,
                                                    mock_setup_et_and_pc, mock_map_alarm_rate_with_nodes,
                                                    mock_setup_alarm_text_and_problem):
        self.fmalarm.MSC_RATE = 1
        self.fmalarm.BSC_RATE = 1
        self.fmalarm.CPP_RATE = 1
        self.fmalarm.SNMP_RATE = 1
        self.fmalarm.AML_RATE = 1
        self.fmalarm.AML_RATIO = 0.5
        teardown_list = [1, 2, 3]
        mock_setup_et_and_pc.return_value = 1, 0
        mock_setup_alarm_burst.side_effect = Exception
        self.fmalarm.configure_fm_alarm_burst([1000], [('TU Synch Reference Loss of Signal', 'major')], Mock(),
                                              '111', teardown_list, 1)
        self.assertTrue(mock_setup_alarm_text_and_problem.called)
        self.assertTrue(mock_setup_et_and_pc.called)
        self.assertTrue(mock_map_alarm_rate_with_nodes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils.deallocate_unused_nodes")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute')
    def test_deallocate_unused_nodes(self, mock_nodes, mock_unused, *_):
        mock_nodes.return_value = [self.used_node, self.unused_node]
        self.generic.deallocate_unused_nodes_and_update_profile_persistence([self.used_node])
        self.assertTrue(mock_unused.called)

    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils.deallocate_unused_nodes")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes_throws_exception(self, mock_error, mock_nodes, mock_deallocate, _):
        mock_deallocate.side_effect = Exception()
        mock_nodes.return_value = [Mock()]
        self.generic.deallocate_unused_nodes_and_update_profile_persistence(mock_nodes)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile.Profile.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils.deallocate_unused_nodes")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute')
    def test_deallocate_IPV6_nodes(self, mock_nodes, mock_unused, *_):
        mock_nodes.return_value = [self.node]
        self.generic.deallocate_IPV6_nodes_and_update_profile_persistence()
        self.assertTrue(mock_unused.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.check_sync_and_remove', return_value=([Mock], []))
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    def test_get_synchronised_nodes__success(self, mock_add_error, _):
        self.assertEqual(1, len(self.generic.get_synchronised_nodes([Mock()], [Mock()])))
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.check_sync_and_remove',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    def test_get_synchronised_nodes__returns_list_if_exception(self, mock_add_error, _):
        self.assertEqual([], self.generic.get_synchronised_nodes([Mock()], Mock()))
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.check_sync_and_remove',
           return_value=([Mock], [Mock()]))
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    def test_get_synchronised_nodes__logs_unsynced_nodes(self, mock_add_error, mock_debug, _):
        self.generic.get_synchronised_nodes([Mock()], [Mock()])
        self.assertEqual(0, mock_add_error.call_count)
        mock_debug.assert_called_with("Removing 1 non-managed nodes on this iteration.")

    # get_synced_pm_enabled_nodes test cases
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute")
    def test_get_allocated_synced_pm_enabled_nodes__is_successful(self, mock_get_nodes_list_by_attribute,
                                                                  mock_get_synchronised_nodes,
                                                                  mock_get_pm_function_enabled_nodes):
        mock_get_nodes_list_by_attribute.return_value = self.nodes_list
        mock_get_synchronised_nodes.return_value = self.nodes_list[:2]
        mock_get_pm_function_enabled_nodes.return_value = self.nodes_list[:2], [self.nodes_list[2]]
        self.assertEqual(self.nodes_list[:2], self.generic.get_allocated_synced_pm_enabled_nodes(self.user))
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "primary_type", "poid",
                                                                             "profiles"])
        mock_get_pm_function_enabled_nodes.assert_called_with(self.nodes_list[:2], self.user)
        mock_get_synchronised_nodes.assert_called_with(self.nodes_list, self.user)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute")
    def test_get_allocated_synced_pm_enabled_nodes__if_nodes_not_existed(self, mock_get_nodes_list_by_attribute,
                                                                         mock_get_synchronised_nodes,
                                                                         mock_get_pm_function_enabled_nodes):
        mock_get_nodes_list_by_attribute.return_value = []
        self.assertRaises(EnvironError, self.generic.get_allocated_synced_pm_enabled_nodes, self.user)
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "primary_type", "poid",
                                                                             "profiles"])
        self.assertFalse(mock_get_synchronised_nodes.called)
        self.assertFalse(mock_get_pm_function_enabled_nodes.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute")
    def test_get_allocated_synced_pm_enabled_nodes__if_synced_nodes_not_existed(self, mock_get_nodes_list_by_attribute,
                                                                                mock_get_synchronised_nodes,
                                                                                mock_get_pm_function_enabled_nodes):
        mock_get_nodes_list_by_attribute.return_value = self.nodes_list
        mock_get_synchronised_nodes.return_value = []
        self.assertRaises(EnvironError, self.generic.get_allocated_synced_pm_enabled_nodes, self.user)
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "primary_type", "poid",
                                                                             "profiles"])
        mock_get_synchronised_nodes.assert_called_with(self.nodes_list, self.user)
        self.assertFalse(mock_get_pm_function_enabled_nodes.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_pm_function_enabled_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute")
    def test_get_synced_pm_enabled_nodes__if_pm_enabled_nodes_not_existed(self, mock_get_nodes_list_by_attribute,
                                                                          mock_get_synchronised_nodes,
                                                                          mock_get_pm_function_enabled_nodes):
        mock_get_nodes_list_by_attribute.return_value = self.nodes_list
        mock_get_synchronised_nodes.return_value = self.nodes_list[:2]
        mock_get_pm_function_enabled_nodes.return_value = [], [self.nodes_list[:2]]
        self.assertRaises(EnvironError, self.generic.get_allocated_synced_pm_enabled_nodes, self.user)
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "primary_type", "poid",
                                                                             "profiles"])
        mock_get_synchronised_nodes.assert_called_with(self.nodes_list, self.user)
        mock_get_pm_function_enabled_nodes.assert_called_with(self.nodes_list[:2], self.user)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_nodes_by_cell_size')
    def test_get_nodes_with_required_number_of_cells__successful(self, mock_get_nodes_by_cell_size, mock_nodes_list, _):
        self.generic.NUMBER_OF_CELLS = 3
        node, node1, node2, node3, node4 = Mock(), Mock(), Mock(), Mock(), Mock()
        node.node_name = "ERBS"
        node1.node_name = "ERBS1"
        node2.node_name = "ERBS2"
        node3.node_name = "ERBS4"
        node4.node_name = "ERBS5"
        mock_get_nodes_by_cell_size.return_value = ["ERBS1", "ERBS5", "ERBS"]
        mock_nodes_list.return_value = [node, node1, node2, node3, node4]
        node_lists = self.generic.get_nodes_with_required_number_of_cells()
        self.assertEqual(len(node_lists), 3)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_workload_admin_user')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_nodes_by_cell_size')
    def test_get_nodes_with_required_number_of_cells__raises_EnvironError(self, mock_get_nodes_by_cell_size, *_):
        self.generic.NUMBER_OF_CELLS = 3
        node, node1, node2, node3, node4 = Mock(), Mock(), Mock(), Mock(), Mock()
        node.node_name = "ERBS"
        node1.node_name = "ERBS1"
        node2.node_name = "ERBS2"
        node3.node_name = "ERBS4"
        node4.node_name = "ERBS5"
        mock_get_nodes_by_cell_size.side_effect = Exception
        self.assertRaises(EnvironError, self.generic.get_nodes_with_required_number_of_cells)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.datetime.datetime")
    def test_get_end_time__success(self, mock_datetime):
        now = datetime.now().replace(hour=8)
        mock_datetime.now.return_value = now
        mock_datetime.now.replace.return_value = now.replace(hour=18, minute=0, second=0)
        mock_datetime.strptime.return_value = now.replace(hour=18, minute=0, second=0)
        end_time = self.generic.get_end_time()
        self.assertEqual(end_time, now.replace(hour=18, minute=0, second=0))

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.datetime.datetime")
    def test_get_end_time__sleep_until_next_day(self, mock_datetime, *_):
        now = datetime.now().replace(hour=19)
        mock_datetime.now.return_value = now
        mock_datetime.now.replace.return_value = now.replace(hour=18, minute=0, second=0)
        mock_datetime.strptime.return_value = now.replace(hour=18, minute=0, second=0)
        end_time = self.generic.get_end_time()
        self.assertEqual(end_time, now.replace(hour=18, minute=0, second=0) + timedelta(days=1))

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes__is_successful_when_there_are_unused_nodes(
            self, mock_error_as_exception, mock_shmutils, *_):
        unused_nodes = [Mock()]
        nodes_list = [Mock()]
        self.generic.update_profile_persistence_nodes_list(unused_nodes, nodes_list)
        mock_shmutils.deallocate_unused_nodes.assert_called_with(unused_nodes, self.generic)
        self.assertFalse(mock_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes__is_successful_when_there_are_no_unused_nodes(
            self, mock_error_as_exception, mock_shmutils, *_):
        unused_nodes = []
        nodes_list = [Mock()]
        self.generic.update_profile_persistence_nodes_list(unused_nodes, nodes_list)
        self.assertFalse(mock_shmutils.deallocate_unused_nodes.called)
        self.assertFalse(mock_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes__add_error_if_cannot_deallocated_nodes(
            self, mock_error_as_exception, mock_shmutils, *_):
        unused_nodes = [Mock()]
        nodes_list = [Mock()]
        mock_shmutils.deallocate_unused_nodes.side_effect = Exception()
        self.generic.update_profile_persistence_nodes_list(unused_nodes, nodes_list)
        mock_shmutils.deallocate_unused_nodes.assert_called_with(unused_nodes, self.generic)
        self.assertTrue(mock_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils')
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes__is_successful_if_unused_nodes_existed_and_node_list_none(self,
                                                                                               mock_error_as_exception,
                                                                                               mock_shmutils,
                                                                                               mock_debug_log, _):
        unused_nodes = [Mock()]
        self.generic.update_profile_persistence_nodes_list(unused_nodes)
        mock_shmutils.deallocate_unused_nodes.assert_called_with(unused_nodes, self.generic)
        self.assertFalse(mock_error_as_exception.called)
        self.assertEqual(2, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes__is_successful_if_unused_nodes_not_existed_and_node_list_none(
            self, mock_error_as_exception, mock_shmutils, mock_debug_log, _):
        unused_nodes = []
        self.generic.update_profile_persistence_nodes_list(unused_nodes)
        self.assertFalse(mock_shmutils.deallocate_unused_nodes.called)
        self.assertFalse(mock_error_as_exception.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils")
    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    def test_deallocate_unused_nodes__add_error_if_cannot_deallocated_nodes_and_node_list_none(
            self, mock_error_as_exception, mock_shmutils, mock_debug_log, _):
        unused_nodes = [Mock()]
        mock_shmutils.deallocate_unused_nodes.side_effect = Exception()
        self.generic.update_profile_persistence_nodes_list(unused_nodes)
        mock_shmutils.deallocate_unused_nodes.assert_called_with(unused_nodes, self.generic)
        self.assertTrue(mock_error_as_exception.called)
        self.assertEqual(1, mock_debug_log.call_count)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils.deallocate_unused_nodes")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    def test_update_profile_persistence_nodes_list__verify_no_negative_nodes(self, mock_log, *_):
        unused_nodes = [Mock()]
        nodes_list = [Mock(), Mock()]
        self.generic.update_profile_persistence_nodes_list(unused_nodes, nodes_list)
        verify_nodes = self.generic.num_nodes
        self.assertEqual(1, verify_nodes)
        self.assertEqual(2, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.persist')
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.SHMUtils.deallocate_unused_nodes")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    def test_update_profile_persistence_nodes_list__no_nodes(self, mock_log, *_):
        unused_nodes = []
        nodes_list = []
        self.generic.update_profile_persistence_nodes_list(unused_nodes, nodes_list)
        verify_nodes = self.generic.num_nodes
        self.assertEqual(0, verify_nodes)
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor")
    def test_get_allocated_nodes__is_successful_if_service_is_used(self, mock_nodemanager_adaptor):
        mock_nodemanager_adaptor.can_service_be_used.return_value = True
        self.generic.get_allocated_nodes("some_profile")
        mock_nodemanager_adaptor.can_service_be_used.assert_called_with(self.generic)
        mock_nodemanager_adaptor.get_list_of_nodes_from_service.assert_called_with("some_profile",
                                                                                   node_attributes=["all"])

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor")
    def test_get_allocated_nodes__is_successful_if_service_is_not_used(
            self, mock_nodemanager_adaptor, mock_node_pool_mgr):
        mock_nodemanager_adaptor.can_service_be_used.return_value = False
        self.generic.get_allocated_nodes("some_profile")
        mock_nodemanager_adaptor.can_service_be_used.assert_called_with(self.generic)
        mock_node_pool_mgr.get_pool.return_value.allocated_nodes.assert_called_with("some_profile")

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor")
    def test_get_allocated_nodes__adds_error_if_cannot_allocated_nodes(
            self, mock_nodemanager_adaptor, mock_node_pool_mgr, mock_add_error_as_exception):
        mock_nodemanager_adaptor.can_service_be_used.return_value = False
        mock_node_pool_mgr.get_pool.return_value.allocated_nodes.side_effect = Exception()
        self.generic.get_allocated_nodes("some_profile")
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor")
    def test_allocate_specific_nodes_to_profile__is_successful_if_service_can_be_used(
            self, mock_nodemanager_adaptor, mock_node_pool_mgr):
        nodes = [Mock()]
        mock_nodemanager_adaptor.can_service_be_used.return_value = True
        self.generic.allocate_specific_nodes_to_profile(nodes)
        mock_nodemanager_adaptor.allocate_nodes.assert_called_with(profile=self.generic, nodes=nodes)
        self.assertFalse(mock_node_pool_mgr.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor")
    def test_allocate_specific_nodes_to_profile__is_successful_if_service_cannot_be_used(
            self, mock_nodemanager_adaptor, mock_node_pool_mgr):
        nodes = [Mock()]
        mock_nodemanager_adaptor.can_service_be_used.return_value = False
        self.generic.allocate_specific_nodes_to_profile(nodes)
        mock_node_pool_mgr.allocate_nodes.assert_called_with(self.generic, nodes)
        self.assertFalse(mock_nodemanager_adaptor.allocated_nodes.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.node_pool_mgr")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor")
    def test_allocate_specific_nodes_to_profile__adds_error_if_cant_allocate_nodes(
            self, mock_nodemanager_adaptor, mock_node_pool_mgr, mock_add_error_as_exception):
        nodes = [Mock()]
        mock_nodemanager_adaptor.can_service_be_used.return_value = False
        mock_node_pool_mgr.allocate_nodes.side_effect = Exception()
        self.generic.allocate_specific_nodes_to_profile(nodes)
        mock_node_pool_mgr.allocate_nodes.assert_called_with(self.generic, nodes)
        self.assertFalse(mock_nodemanager_adaptor.allocated_nodes.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.netsim_operations.NetsimOperation")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    def test_execute_netsim_command_on_netsim_node_returns_true_if_command_execution_on_netsim_is_successful(
            self, mock_debug_log, mock_netsim_operation):
        mock_netsim_operation.execute_command_string.return_value = True
        self.assertTrue(self.generic.execute_netsim_command_on_netsim_node([Mock(node_id=123)], "some_netsim_command"))
        self.assertTrue(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.netsim_operations.NetsimOperation")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    def test_execute_netsim_command_on_netsim_node_returns_true_if_command_execution_on_netsim_is_unsuccessful(
            self, mock_debug_log, mock_netsim_operation):
        mock_netsim_operation.return_value.execute_command_string.side_effect = Exception
        self.assertFalse(self.generic.execute_netsim_command_on_netsim_node([Mock(node_id=123)], "some_netsim_command"))
        self.assertTrue(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_users")
    def test_create_profile_users__create_user_profile(self, mock_create_users):
        self.generic.create_profile_users(1, ["Shm_Administrator", "Cmedit_Administrator"])
        self.assertTrue(mock_create_users.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.EnmRole")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.CustomUser.is_session_established", return_value=True)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.CustomUser.create")
    def test_create_custom_user_in_enm_is_success(self, mock_create_user, *_):
        self.generic.USER_ROLES = ['role1', 'role2']
        self.generic.CUSTOM_USER_ROLES = ['customrole1', 'customrole2']
        self.generic.CUSTOM_TARGET_GROUPS = ['customtarget1', 'customtarget2']
        self.generic.USER_NAME = 'cephquota_01'
        self.generic.NUMBER_OF_RETRIES = 3
        self.generic.create_custom_user_in_enm(expected_sleep_time=2)
        self.assertTrue(mock_create_user.callled)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.EnmRole")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.time.sleep")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.CustomUser.is_session_established",
           return_value=False)
    def test_create_custom_user_in_enm_is_not_success(self, *_):
        self.generic.USER_ROLES = []
        self.generic.USER_NAME = 'cephquota_01'
        self.generic.NUMBER_OF_RETRIES = 3
        with self.assertRaises(EnmApplicationError):
            self.generic.create_custom_user_in_enm(expected_sleep_time=2)

    def test_generate_configurable_source_ip__ipv4_string(self):
        ipv4_string = self.generic.generate_configurable_source_ip([172, 16, 206, 140])
        self.assertEqual(ipv4_string, "{1}{0}{2}{0}{3}{0}{4}".format(".", "172", "16", "206", "140"))

    def test_get_start_time_today__expected_start_time(self):
        self.generic.SCHEDULED_TIMES_STRINGS = ["12:34:00"]
        expected_start = self.generic.get_start_time_today()
        self.assertEqual(expected_start.hour, 12)
        self.assertEqual(expected_start.minute, 34)
        self.assertEqual(expected_start.second, 0)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.partial')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.download_tls_certs_teardown_operations')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.winfiol_operations.'
           'create_pki_entity_and_download_tls_certs')
    def test_download_tls_certs_for_nodes__success(self, mock_pki_tls, *_):
        self.generic.download_tls_certs([self.user])
        self.assertTrue(mock_pki_tls.called)
        self.assertEqual(mock_pki_tls.call_args[0][0], ([self.user]))

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.partial')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.download_tls_certs_teardown_operations')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.winfiol_operations.'
           'create_pki_entity_and_download_tls_certs')
    def test_download_tls_certs__adds_error_as_exception(self, mock_pki_tls, mock_add_error_as_exception, *_):
        mock_pki_tls.side_effect = Exception
        self.generic.download_tls_certs([self.user])
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.winfiol_operations.perform_revoke_activity')
    def test_download_tls_certs_teardown_operations__success(self, mock_revoke):
        self.generic.download_tls_certs_teardown_operations([self.user])
        self.assertTrue(mock_revoke.called)

    # enable_passwordless_login_for_user test cases

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__if_child_is_none(
            self, mock_pexpect, mock_verify_and_generate_ssh_keys, mock_debug_log, _):
        child = mock_pexpect.spawn()
        child.expect.side_effect = [1, 2]
        child.before = "Now try logging into the machine"
        user = Mock(username="PM_26", password="pwd")
        self.assertTrue(self.generic.enable_passwordless_login_for_user(self, None, user, "ip_a"))
        self.assertTrue(mock_verify_and_generate_ssh_keys.called)
        self.assertEqual(5, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__returns_true_if_auth_and_password_prompts_appear(
            self, mock_pexpect, mock_verify_and_generate_ssh_keys, mock_debug_log, _):
        user = Mock(username="PM_26")
        child = mock_pexpect.spawn().__enter__()
        child.expect.side_effect = [1, 2]
        child.before = "Now try logging into the machine"
        self.is_cloud_native = False
        self.assertTrue(self.generic.enable_passwordless_login_for_user(self, child, user, "ip_a",
                                                                        is_scripting_vm=False))
        self.assertTrue(mock_verify_and_generate_ssh_keys.called)
        self.assertEqual(5, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__returns_true_if_password_prompt_appears(
            self, mock_pexpect, mock_verify_and_generate_ssh_keys, mock_debug_log, _):
        user = Mock(username="PM_26")
        child = mock_pexpect.spawn().__enter__()
        child.expect.side_effect = [1, 2]
        child.before = "Now try logging into the machine"
        self.is_cloud_native = False
        self.assertTrue(self.generic.enable_passwordless_login_for_user(self, child, user, "ip_a", is_scripting_vm=False))
        self.assertTrue(mock_verify_and_generate_ssh_keys.called)
        self.assertEqual(5, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__returns_true_if_no_prompt_appears(
            self, mock_pexpect, mock_verify_and_generate_ssh_keys, mock_debug_log, _):
        user = Mock(username="PM_26")
        child = mock_pexpect.spawn().__enter__()
        child.expect.side_effect = [None, 2]
        child.before = "Now try logging into the machine"
        self.assertTrue(self.generic.enable_passwordless_login_for_user(self, child, user, "ip_a", is_scripting_vm=False))
        self.assertTrue(mock_verify_and_generate_ssh_keys.called)
        self.assertEqual(5, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__returns_true_if_auth_and_password_prompts_appear_on_cloud_native(
            self, mock_pexpect, mock_verify_and_generate_ssh_keys, mock_debug_log, _):
        user = Mock(username="PM_26")
        child = mock_pexpect.spawn().__enter__()
        child.expect.side_effect = [1, 2]
        child.before = "Now try logging into the machine"
        self.assertTrue(self.generic.enable_passwordless_login_for_user(self, child, user, "ip_a", is_scripting_vm=False))
        self.assertTrue(mock_verify_and_generate_ssh_keys.called)
        self.assertEqual(5, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__if_scripting_vm_is_true_on_cloud_native(
            self, mock_pexpect, mock_verify_and_generate_ssh_keys, mock_debug_log, mock_run_local_cmd, _):
        user = Mock(username="PM_26")
        child = mock_pexpect.spawn().__enter__()
        child.expect.side_effect = [1, 2]
        child.before = "Now try logging into the machine"
        mock_run_local_cmd.return_value = str(Mock(rc=0))
        self.assertTrue(self.generic.enable_passwordless_login_for_user(self, child, user, "ip_a", is_scripting_vm=True))
        self.assertTrue(mock_verify_and_generate_ssh_keys.called)
        self.assertEqual(5, mock_debug_log.call_count)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.verify_and_generate_ssh_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect")
    def test_enable_passwordless_login_for_user__returns_false_if_command_timed_out(
            self, mock_pexpect, mock_debug_log, *_):
        user = Mock(username="PM_26")
        child = mock_pexpect.spawn().__enter__()
        child.expect.side_effect = [3]
        self.assertFalse(self.generic.enable_passwordless_login_for_user(self, child, user, "ip_a", is_scripting_vm=False))
        self.assertEqual(4, mock_debug_log.call_count)

    # test_enable_passwordless_login_for_users test cases

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "remove_duplicate_authorized_keys", return_value=True)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "enable_passwordless_login_for_user", return_value=True)
    def test_enable_passwordless_login_for_users__is_successful(
            self, mock_enable_passwordless_login_for_user, mock_remove_duplicate_authorized_keys):
        hosts = ["ip_a", "ip_b"]
        user_1, user_2 = Mock(), Mock()
        child = MagicMock()
        self.generic.enable_passwordless_login_for_users(child, [user_1, user_2], hosts, is_scripting_vm=False)
        self.assertEqual(2, len(mock_enable_passwordless_login_for_user.mock_calls))
        self.assertEqual([call(user_1, "ip_a"), call(user_2, "ip_a")],
                         mock_remove_duplicate_authorized_keys.mock_calls)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "remove_duplicate_authorized_keys", return_value=True)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "enable_passwordless_login_for_user", side_effect=[False, True, False, True])
    def test_enable_passwordless_login_for_users__is_successful_if_problem_with_one_host(
            self, mock_enable_passwordless_login_for_user, mock_remove_duplicate_authorized_keys):
        hosts = ["ip_a", "ip_b"]
        user_1, user_2 = Mock(), Mock()
        child = MagicMock()

        self.generic.enable_passwordless_login_for_users(child, [user_1, user_2], hosts, is_scripting_vm=False)
        self.assertEqual(4, len(mock_enable_passwordless_login_for_user.mock_calls))
        self.assertEqual([call(user_1, "ip_b"), call(user_2, "ip_b")],
                         mock_remove_duplicate_authorized_keys.mock_calls)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "remove_duplicate_authorized_keys")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "enable_passwordless_login_for_user", return_value=False)
    def test_enable_passwordless_login_for_users__is_successful_if_problems_with_all_hosts(
            self, mock_enable_passwordless_login_for_user, mock_remove_duplicate_authorized_keys):
        hosts = ["ip_a", "ip_b"]
        user_1, user_2 = Mock(), Mock()
        child = MagicMock()
        self.generic.enable_passwordless_login_for_users(child, [user_1, user_2], hosts, is_scripting_vm=False)
        self.assertEqual(4, len(mock_enable_passwordless_login_for_user.mock_calls))
        self.assertFalse(mock_remove_duplicate_authorized_keys.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "remove_duplicate_authorized_keys", return_value=True)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
           "enable_passwordless_login_for_user", return_value=True)
    def test_enable_passwordless_login_for_users__if_scripting_vm_true(
            self, mock_enable_passwordless_login_for_user, mock_remove_duplicate_authorized_keys):
        hosts = ["ip_a", "ip_b"]
        user_1, user_2 = Mock(), Mock()
        child = MagicMock()

        self.generic.enable_passwordless_login_for_users(child, [user_1, user_2], hosts, is_scripting_vm=True)
        self.assertEqual(2, len(mock_enable_passwordless_login_for_user.mock_calls))
        self.assertEqual([call(user_1, "ip_a"), call(user_2, "ip_a")],
                         mock_remove_duplicate_authorized_keys.mock_calls)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_remote_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    def test_remove_duplicate_authorized_keys__successful(self, mock_command, mock_run_remote_cmd, _):
        self.assertTrue(self.generic.remove_duplicate_authorized_keys(Mock(username="user1", password="pwd1"), "ip_a"))
        cmd1 = "sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.uniq"
        cmd2 = "mv ~/.ssh/authorized_keys{.uniq,}"
        self.assertEqual([call(cmd1), call(cmd2)], mock_command.mock_calls)
        self.assertEqual(mock_run_remote_cmd.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_remote_cmd",
           side_effect=Exception("some_error"))
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.Command")
    def test_remove_duplicate_authorized_keys__unsuccessful(self, mock_command, mock_run_remote_cmd, mock_debug):
        self.assertFalse(self.generic.remove_duplicate_authorized_keys(Mock(username="user1", password="pwd1"), "ip_a"))
        cmd1 = "sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.uniq"
        self.assertEqual([call(cmd1)], mock_command.mock_calls)
        self.assertEqual(mock_run_remote_cmd.call_count, 1)
        mock_debug.assert_called_with("Failed to remove duplicate keys - some_error")

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.is_enm_on_cloud_native', return_value=True)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect.spawn.expect')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_ms_host')
    def test_switch_to_ms_or_emp__EnvironError(self, *_):
        self.assertRaises(EnvironError, GenericFlow.switch_to_ms_or_emp)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.info')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect.spawn.expect')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_ms_host')
    def test_switch_to_ms_or_emp__Success(self, *_):
        GenericFlow.switch_to_ms_or_emp()

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.is_emp', return_value=True)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_emp', return_value="host1")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect.spawn.expect')
    def test_switch_to_ms_or_emp__is_emp(self, mock_pexpect_spawn, mock_get_emp, mock_logger_debug, *_):
        mock_get_emp.return_value = 'localhost'
        GenericFlow.switch_to_ms_or_emp()
        self.assertTrue(mock_pexpect_spawn.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.is_emp', return_value=False)
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.get_emp', return_value="host1")
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.pexpect.spawn.expect', side_effect=Exception)
    def test_switch_to_ms_or_emp__Exception(self, *_):
        self.assertRaises(EnvironError, GenericFlow.switch_to_ms_or_emp)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    def test_verify_and_generate_ssh_keys__is_enm_on_cloud_native(self, mock_debug_log):
        verify_and_generate_ssh_keys(self, "abc")
        self.assertTrue(mock_debug_log.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.create_ssh_keys")
    def test_verify_and_generate_ssh_keys__is_enm_on_physical_or_cloud(self, mock_create_ssh_keys):
        self.is_cloud_native = False
        verify_and_generate_ssh_keys(self, "abc")
        self.assertTrue(mock_create_ssh_keys.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=True)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.update_poids")
    def test_update_nodes_with_poid_info__success_if_service_used(self, mock_update_poids, *_):
        flow = GenericFlow()
        flow.update_nodes_with_poid_info()
        self.assertTrue(mock_update_poids.called)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.update_poid_attribute_on_nodes", return_value=0)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.update_cached_nodes_list")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.build_poid_dict_from_enm_data")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.update_poids")
    def test_update_nodes_with_poid_info__success_if_service_not_used_and_no_failures_occurred(
            self, mock_update_poids, mock_build_poid_dict_from_enm_data, mock_update_cached_nodes_list,
            mock_update_poid_attribute_on_nodes, *_):
        flow = GenericFlow()
        flow.update_nodes_with_poid_info()
        self.assertFalse(mock_update_poids.called)
        self.assertTrue(mock_build_poid_dict_from_enm_data.called)
        self.assertTrue(mock_update_cached_nodes_list.called)
        mock_update_poid_attribute_on_nodes.assert_called_with(mock_build_poid_dict_from_enm_data.return_value)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.nodemanager_service_can_be_used",
           new_callable=PropertyMock, return_value=False)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.__init__", return_value=None)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.update_poid_attribute_on_nodes", return_value=1)
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.update_cached_nodes_list")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.build_poid_dict_from_enm_data")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.nodemanager_adaptor.update_poids")
    def test_update_nodes_with_poid_info__success_if_service_not_used_and_failures_occurred(
            self, mock_update_poids, mock_build_poid_dict_from_enm_data, mock_update_cached_nodes_list,
            mock_update_poid_attribute_on_nodes, *_):
        flow = GenericFlow()
        self.assertRaises(EnvironError, flow.update_nodes_with_poid_info)
        self.assertFalse(mock_update_poids.called)
        self.assertTrue(mock_build_poid_dict_from_enm_data.called)
        self.assertTrue(mock_update_cached_nodes_list.called)
        mock_update_poid_attribute_on_nodes.assert_called_with(mock_build_poid_dict_from_enm_data.return_value)

    # get_supported_data_types_from_fls test cases
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    def test_get_supported_data_types_from_fls__if_physical(self, mock_run_cmd_on_ms,
                                                            mock_get_active_postgres_db_hostname, *_):
        self.is_cloud_native = False
        response = """data_type
        ---------------------
        PM_CELLTRACE
         PM_CELLTRACE_CUCP
         PM_CELLTRACE_CUUP
         PM_CELLTRACE_DU
         PM_CTUM
         PM_EBM
         PM_STATISTICAL
         PM_STATISTICAL_1MIN
         PM_UETRACE
         TOPOLOGY_5GCORE
         TOPOLOGY_ASSOC
         TOPOLOGY_BULK_CM
         TOPOLOGY_CORE
         TOPOLOGY_IMS
         TOPOLOGY_LTE
         TOPOLOGY_NR
         TOPOLOGY_SharedCNF
         TOPOLOGY_TCIM
         TOPOLOGY_TRANSPORT
         TOPOLOGY_TWAMP
        (20 rows)
        """
        mock_get_active_postgres_db_hostname.return_value = "ieatrcxb6248"
        mock_run_cmd_on_ms.return_value = Mock(stdout=response, rc=0)
        get_supported_data_types_from_fls(self)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    def test_get_supported_data_types_from_fls__raises_env_error_if_unable_to_get_db_hostname(
            self, mock_run_cmd_on_ms, mock_get_active_postgres_db_hostname, *_):
        self.is_cloud_native = False
        mock_get_active_postgres_db_hostname.side_effect = EnvironError("error")
        mock_run_cmd_on_ms.return_value = Mock(stdout="something is wrong", rc=1)
        self.assertRaises(EnvironError, get_supported_data_types_from_fls, self)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 0)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    def test_get_supported_data_types_from_fls__if_physical_raises_env_error(self, mock_run_cmd_on_ms,
                                                                             mock_get_active_postgres_db_hostname, *_):
        self.is_cloud_native = False
        mock_get_active_postgres_db_hostname.return_value = "ieatrcxb6248"
        mock_run_cmd_on_ms.side_effect = [Mock(stdout="something is wrong", rc=1)]
        self.assertRaises(EnvironError, get_supported_data_types_from_fls, self)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace",
           return_value="enm3")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    def test_get_supported_data_types_from_fls__if_cenm(self, mock_run_local_cmd, *_):
        self.is_cloud_native = True
        self.is_physical = False
        response = """PM_CELLTRACE
        PM_CTUM
        PM_STATISTICAL"""
        mock_run_local_cmd.side_effect = [Mock(stdout=response, rc=0)]
        get_supported_data_types_from_fls(self)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace",
           return_value="enm3")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    def test_get_supported_data_types_from_fls__if_cenm_raises_env_error(self, mock_run_local_cmd, *_):
        self.is_cloud_native = True
        self.is_physical = False
        mock_run_local_cmd.return_value = Mock(stdout="", rc=1)
        self.assertRaises(EnvironError, get_supported_data_types_from_fls, self)
        self.assertEqual(mock_run_local_cmd.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address",
           retun_value="1.1.1.1")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    def test_get_supported_data_types_from_fls__if_cloud(self, mock_run_cmd_on_vm, *_):
        self.is_cloud_native = False
        self.is_physical = False
        response = """data_type
        ---------------------
        PM_CELLTRACE
        PM_CELLTRAFFIC
        PM_CTUM
        PM_EBM
        PM_GPEH
        PM_STATISTICAL
        PM_STATISTICAL_1MIN
        PM_UETR
        PM_UETRACE
        (9 rows)"""
        mock_run_cmd_on_vm.side_effect = [Mock(stdout=response, rc=0)]
        get_supported_data_types_from_fls(self)
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_active_postgres_db_hostname")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_enm_cloud_native_namespace",
           return_value="enm3")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment.get_cloud_members_ip_address",
           retun_value="1.1.1.1")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_local_cmd")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_vm")
    def test_get_supported_data_types_from_fls__if_cloud_raises_env_error(self, mock_run_cmd_on_vm, *_):
        self.is_cloud_native = False
        self.is_physical = False
        mock_run_cmd_on_vm.return_value = Mock(stdout="", rc=1)
        self.assertRaises(EnvironError, get_supported_data_types_from_fls, self)
        self.assertEqual(mock_run_cmd_on_vm.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_supported_data_types_from_fls")
    def test_get_matched_supported_datatypes_with_configured_datatypes__is_successful(self, mock_supported_datatypes,
                                                                                      mock_debug_log):
        mock_supported_datatypes.return_value = ["PM_STATISTICAL", "PM_UETR", "PM_CTUM", "TOPOLOGY_TCIM",
                                                 "TOPOLOGY_TRANSPORT"]
        self.assertEqual(['PM_STATISTICAL', 'PM_UETR', 'TOPOLOGY_*'],
                         get_matched_supported_datatypes_with_configured_datatypes(self))
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_supported_datatypes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.get_supported_data_types_from_fls")
    def test_get_matched_supported_datatypes_with_configured_datatypes__raise_env_error(self, mock_supported_datatypes,
                                                                                        mock_debug_log):
        mock_supported_datatypes.return_value = ["PM_CTUM", " PM_EBM"]
        self.assertRaises(EnvironError, get_matched_supported_datatypes_with_configured_datatypes, self)
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_supported_datatypes.call_count, 1)

    # get_active_postgres_db_hostname test cases
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    def test_get_active_postgres_db_hostname__is_successful(self, mock_run_cmd_on_ms, mock_debug_log):
        db_host_info = ("db_cluster         Grp_CS_db_cluster_postgres_clustered_service  ieatrcxb6248  "
                        "active-standby          lsb        ONLINE          OK       -")
        mock_run_cmd_on_ms.return_value = Mock(stdout=db_host_info, rc=0)
        get_active_postgres_db_hostname()
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.shell.run_cmd_on_ms")
    def test_get_active_postgres_db_hostname__if_active_db_not_found(self, mock_run_cmd_on_ms, mock_debug_log):
        mock_run_cmd_on_ms.return_value = Mock(stdout="error", rc=1)
        self.assertRaises(EnvironError, get_active_postgres_db_hostname)
        self.assertEqual(mock_run_cmd_on_ms.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 0)

    # is_enm_on_rack test cases
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment."
           "get_values_from_global_properties", return_value="Extra_Large_ENM_On_Rack_Servers")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    def test_is_enm_on_rack__returns_true(self, mock_debug_log, _):
        self.assertTrue(is_enm_on_rack())
        self.assertEqual(mock_debug_log.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.enm_deployment."
           "get_values_from_global_properties", return_value="Large_ENM")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug")
    def test_is_enm_on_rack__returns_false(self, mock_debug_log, _):
        self.assertFalse(is_enm_on_rack())
        self.assertEqual(mock_debug_log.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
