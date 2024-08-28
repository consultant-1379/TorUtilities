#!/usr/bin/env python
from datetime import datetime
import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class ShmFlowUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.nodes_list = [Mock(primary_type="ERBS"), Mock(primary_type="ERBS")]
        self.nodes_list_2 = [Mock(node_id="LTE45dg2ERBS00069"), Mock(node_id="LTE45dg2ERBS00023")]
        self.flow = ShmFlow()
        self.flow.DEFAULT = True
        self.flow.LOG_ONLY = True
        self.flow.JOB_NAME_PREFIX = "test"
        self.flow.REBOOT_NODE = 'true'
        self.flow.SKIP_SYNC_CHECK = False
        self.flow.NODES_PER_HOST = 2
        self.flow.MAX_NODES = 1
        self.flow.PIB_VALUES = {"SMRS_BSC_NoOf_BACKUP_FILES": "2"}
        self.flow.PKG_PIB_VALUES = {"SOFTWARE_PACKAGE_LOCK_EXPIRY_IN_DAYS": "1"}
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.enm_annotate_method')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_get_started_annotated_nodes_enm_annotate_adds_exception(self, mock_add_exception, mock_enm_annotate_method, *_):
        mock_enm_annotate_method.side_effect = self.exception
        self.flow.get_started_annotated_nodes(user=self.user, nodes=self.nodes_list)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.enm_annotate_method')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.start_stopped_nodes_or_remove')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_get_started_annotated_nodes_adds_exception(self, mock_add_exception, mock_start_stopped_nodes_or_remove, *_):
        mock_start_stopped_nodes_or_remove.side_effect = self.exception
        self.flow.get_started_annotated_nodes(user=self.user, nodes=self.nodes_list)
        self.assertTrue(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.enm_annotate_method')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.start_stopped_nodes_or_remove')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_get_started_annotated_nodes(self, mock_add_exception, *_):
        self.flow.get_started_annotated_nodes(user=self.user, nodes=self.nodes_list)
        self.assertFalse(mock_add_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.upgrade_setup')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_create_upgrade_job_adds_error(self, mock_add_error_as_exception, mock_check_sync_and_remove, *_):
        mock_check_sync_and_remove.side_effect = self.exception
        self.flow.create_upgrade_job(user=self.user, nodes=self.nodes_list)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.upgrade_setup')
    def test_create_upgrade_job__success(self, mock_upgrade_setup, *_):
        self.flow.create_upgrade_job(user=self.user, nodes=self.nodes_list)
        self.assertTrue(mock_upgrade_setup.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.assign_nodes_based_on_profile_specification',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_started_annotated_nodes',
           return_value=[Mock(), Mock()])
    def test_return_highest_mim_count_started_nodes_success(self, *_):
        high_mim_count_nodes = self.flow.return_highest_mim_count_started_nodes(self.user, self.nodes_list)
        self.assertEqual(2, len(high_mim_count_nodes))

    def test_return_highest_mim_count_started_nodes_no_nodes(self):
        self.flow.return_highest_mim_count_started_nodes(self.user, nodes_list=[])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.get_inventory_sync_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.supervise')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep', return_value=None)
    def test_inventory_sync_nodes__success(self, *_):
        self.flow.TIMEOUT = 1
        self.flow.inventory_sync_nodes(self.user, self.nodes_list)

    def test_inventory_sync_nodes__no_nodes(self):
        self.flow.inventory_sync_nodes(self.user, nodes=[])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.get_inventory_sync_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmManagement.supervise')
    def test_inventory_sync_nodes__failure(self, *_):
        self.assertRaises(EnmApplicationError, self.flow.inventory_sync_nodes, self.user, self.nodes_list)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_synced_nodes', return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.group_nodes_per_netsim_host',
           return_value={"node1": "lte_01", "node2": "lte_02", "node3": "lte_03"})
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    def test_get_filtered_nodes_per_host__success(self, *_):
        filtered_nodes = self.flow.get_filtered_nodes_per_host(self.nodes_list)
        self.assertEqual(2, len(filtered_nodes))

    def test_get_filtered_nodes_per_host__no_nodes(self):
        self.flow.get_filtered_nodes_per_host(started_nodes=[])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmBackUpCleanUpJob.create')
    def test_cleanup_after_upgrade__success(self, mock_create, _):
        self.flow.cleanup_after_upgrade(self.user, self.nodes_list)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmBackUpCleanUpJob.create', side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_cleanup_after_upgrade__adds_exception(self, mock_error, mock_create, _):
        self.flow.cleanup_after_upgrade(self.user, self.nodes_list)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobSpitFire.wait_time_for_job_to_complete')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmBackUpCleanUpJob.create')
    @patch('enmutils_int.lib.shm_backup_jobs.BackupJobSpitFire')
    def test_execute_backup_jobs(self, mock_backup_job, mock_clean_up_job, mock_wait_time_for_job_to_complete,
                                 mock_error, *_):
        mock_backup_job.side_effect = [None, self.exception]
        mock_clean_up_job.create.side_effect = self.exception
        mock_wait_time_for_job_to_complete.side_effect = self.exception
        self.flow.execute_backup_jobs(mock_backup_job, mock_clean_up_job, self.user)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmBackUpCleanUpJob.wait_time_for_job_to_complete')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmBackUpCleanUpJob')
    def test_execute_backup_jobs_exception(self, mock_clean_up_job,
                                           mock_wait_time_for_job_to_complete, mock_error, *_):
        mock_backup_job = Mock()
        mock_backup_job.side_effect = [None, self.exception]
        mock_clean_up_job.create.side_effect = self.exception
        mock_wait_time_for_job_to_complete.side_effect = [None, self.exception]
        self.flow.execute_backup_jobs(mock_backup_job, mock_clean_up_job, self.user)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    def test_get_synced_nodes__if_profile_name_is_shm_06(self, mock_get_sync, *_):
        mock_get_sync.return_value = self.nodes_list
        self.flow.get_synced_nodes(self.nodes_list, nodes_required=1, profile_name="SHM_06")

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    def test_get_synced_nodes_more_synced(self, mock_get_sync, *_):
        mock_get_sync.return_value = self.nodes_list
        self.flow.get_synced_nodes(self.nodes_list, nodes_required=1)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    def test_get_synced_nodes_equally_synced(self, mock_get_sync, *_):
        mock_get_sync.return_value = self.nodes_list
        self.flow.get_synced_nodes(self.nodes_list, nodes_required=2)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    def test_get_synced_nodes_less_synced(self, mock_get_sync, mock_debug, *_):
        mock_get_sync.return_value = self.nodes_list
        self.flow.get_synced_nodes(self.nodes_list, nodes_required=3)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes')
    def test_get_synced_nodes_unsynced(self, mock_get_unsync, *_):
        mock_get_unsync.return_value = []
        self.flow.get_synced_nodes(self.nodes_list, nodes_required=0)

    def test_get_synced_nodes_no_nodes(self):
        self.flow.get_synced_nodes(node_list=[], nodes_required=0)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_delete_inactive_upgrade_packages_throws_index_error(self, mock_error):
        self.flow.delete_inactive_upgrade_packages(self.user, [])
        self.assertTrue(mock_error.called)

    @ParameterizedTestCase.parameterize(
        ("int_time", "expected"),
        [
            (0, "00:00:00"),
            (58260, "16:11:00"),
            (86400, "24:00:00"),
            (19413, "05:23:33"),
        ]
    )
    def test_convert_seconds_to_time_string__returns_correct_time(self, int_time, expected):
        self.assertEqual(expected, self.flow.convert_seconds_to_time_string(int_time))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.convert_seconds_to_time_string')
    def test_convert_shm_scheduled_times__success(self, mock_convert):
        scheduled_time = ["06:30:00", 58260]
        self.flow.convert_shm_scheduled_times(scheduled_time)
        self.assertEqual(mock_convert.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.determine_highest_mim_count_nodes")
    def test_assign_nodes_based_on_profile_specification__is_successful_for_shm_03(self, _):
        self.flow.NAME = "SHM_03"
        self.flow.assign_nodes_based_on_profile_specification(self.user, self.nodes_list)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.SHMUtils.determine_highest_model_identity_count_nodes")
    def test_assign_nodes_based_on_profile_specification__is_successful_for_shm_05(self, _):
        self.flow.NAME = "SHM_05"
        self.flow.assign_nodes_based_on_profile_specification(self.user, self.nodes_list)

    def test_assign_nodes_based_on_profile_specification__verify_successful_for_single_upgrade_profiles(self):
        self.flow.NAME = "SHM_31"
        self.flow.assign_nodes_based_on_profile_specification(self.user, self.nodes_list)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_nodes_list_by_attribute')
    def test_assign_nodes_based_on_profile_specification_is_successful_for_other_profiles(self, _):
        self.flow.NAME = "XYZ_01"
        self.flow.assign_nodes_based_on_profile_specification(self.user, self.nodes_list)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.return_highest_mim_count_started_nodes',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_filtered_nodes_per_host',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__upgrade_profiles(self, mock_pib_update, *_):
        self.flow.NAME = "SHM_03"
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertTrue(mock_pib_update.called)
        self.assertEqual(2, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_started_annotated_nodes',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_synced_nodes', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__backup_profiles(self, mock_pib_update, *_):
        self.flow.NAME = "SHM_01"
        self.flow.MAX_NODES = 1
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertTrue(mock_pib_update.called)
        self.assertEqual(1, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.return_highest_mim_count_started_nodes',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_filtered_nodes_per_host',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__shm_27(self, mock_pib_update, *_):
        self.flow.NAME = "SHM_27"
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertTrue(mock_pib_update.called)
        self.assertEqual(2, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.return_highest_mim_count_started_nodes',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.inventory_sync_nodes',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.'
           'deallocate_unused_nodes_and_update_profile_persistence')
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__shm_31(self, *_):
        self.flow.NAME = "SHM_31"
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertEqual(2, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_started_annotated_nodes',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.set_primary_core_baseband_FRU',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__shm_47(self, *_):
        self.flow.NAME = "SHM_47"
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertEqual(2, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_started_annotated_nodes',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.inventory_sync_nodes', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_filtered_nodes_per_host',
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__shm_32(self, mock_pib_update, *_):
        self.flow.NAME = "SHM_32"
        self.flow.MAX_NODES = 1
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertTrue(mock_pib_update.called)
        self.assertEqual(1, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__other_profiles(self, mock_pib_update, *_):
        self.flow.NAME = "SHM_00"
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertTrue(mock_pib_update.called)
        self.assertEqual(1, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.return_highest_mim_count_started_nodes',
           side_effect=Exception)
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__raises_enm_application_error(self, mock_pib_update, *_):
        self.flow.NAME = "SHM_03"
        self.assertRaises(EnmApplicationError, self.flow.select_nodes_based_on_profile_name, self.user)
        self.assertTrue(mock_pib_update.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_node_attributes_based_on_profile_name',
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.check_and_update_pib_values_for_backups")
    def test_select_nodes_based_on_profile_name__no_nodes(self, mock_pib_update, *_):
        synced_nodes = self.flow.select_nodes_based_on_profile_name(self.user)
        self.assertTrue(mock_pib_update.called)
        self.assertEqual(0, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    def test_select_node_attributes_based_on_profile_name__success_for_shm01(self, mock_get_nodes_list_by_attribute):
        self.flow.NAME = "SHM_01"
        nodes_list = self.flow.select_node_attributes_based_on_profile_name()
        self.assertEqual(2, len(nodes_list))
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=['node_id', 'node_ip', 'netsim', 'poid', 'primary_type', 'mim_version', 'simulation',
                             'node_name'])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    def test_select_node_attributes_based_on_profile_name__success_for_shm05(self, mock_get_nodes_list_by_attribute):
        self.flow.NAME = "SHM_05"
        nodes_list = self.flow.select_node_attributes_based_on_profile_name()
        self.assertEqual(2, len(nodes_list))
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=['node_id', 'node_ip', 'netsim', 'poid', 'primary_type', 'mim_version', 'simulation',
                             'node_name', 'model_identity'])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    def test_select_node_attributes_based_on_profile_name__success_for_shm33(self, mock_get_nodes_list_by_attribute):
        self.flow.NAME = "SHM_33"
        nodes_list = self.flow.select_node_attributes_based_on_profile_name()
        self.assertEqual(2, len(nodes_list))
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=['node_id', 'node_ip', 'netsim', 'poid', 'primary_type', 'mim_version', 'simulation',
                             'node_name'])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    def test_select_node_attributes_based_on_profile_name__success_for_asu_01(self, mock_get_nodes_list_by_attribute):
        self.flow.NAME = "ASU_01"
        nodes_list = self.flow.select_node_attributes_based_on_profile_name()
        self.assertEqual(2, len(nodes_list))
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=['node_id', 'node_ip', 'netsim', 'poid', 'primary_type', 'mim_version', 'simulation',
                             'node_name', 'model_identity'])

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    def test_select_node_attributes_based_on_profile_name__success_for_shm03(self, mock_get_nodes_list_by_attribute):
        self.flow.NAME = "SHM_03"
        nodes_list = self.flow.select_node_attributes_based_on_profile_name()
        self.assertEqual(2, len(nodes_list))
        mock_get_nodes_list_by_attribute.assert_called_with(
            node_attributes=['node_id', 'node_ip', 'netsim', 'poid', 'primary_type', 'mim_version', 'simulation',
                             'node_name', 'profiles'])

    def test_set_primary_core_baseband_FRU__success(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'SUCCESS FDN : SubNetwork=Europe,'
                                                                      u'SubNetwork=Ireland,SubNetwork=NETSimW,'
                                                                      u'ManagedElement=LTE46dg2ERBS00070,'
                                                                      u'NodeSupport=1,MpClusterHandling=1',
                                                                      u'', u'', u'1 instance(s) updated']
        self.flow.set_primary_core_baseband_FRU(self.user, self.nodes_list_2)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    def test_set_primary_core_baseband_FRU__failed(self, mock_error):
        self.user.enm_execute.return_value.get_output.return_value = [u'FAILED FDN : SubNetwork=Europe,'
                                                                      u'SubNetwork=Ireland,SubNetwork=NETSimW,'
                                                                      u'ManagedElement=LTE07dg2ERBS00002,NodeSupport=1,'
                                                                      u'MpClusterHandling=1']
        self.flow.set_primary_core_baseband_FRU(self.user, self.nodes_list_2)
        self.assertTrue(mock_error.called)

    def test_set_primary_core_baseband_FRU__all_nodes_set(self):
        self.user.enm_execute.return_value.get_output.return_value = [u'SUCCESS FDN : SubNetwork=Europe,'
                                                                      u'SubNetwork=Ireland,SubNetwork=NETSimW,'
                                                                      u'ManagedElement=LTE46dg2ERBS00070,'
                                                                      u'NodeSupport=1,MpClusterHandling=1',
                                                                      u'', u'', u'1 instance(s) updated']
        self.flow.MAX_NODES = 2
        self.flow.set_primary_core_baseband_FRU(self.user, nodes_list=self.nodes_list_2)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_nodes_based_on_profile_name',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[Mock(), Mock()])
    def test_select_required_number_of_nodes_for_profile__sleep_until_day(self, *_):
        synced_nodes = self.flow.select_required_number_of_nodes_for_profile(self.user, "day")
        self.assertEqual(2, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_nodes_based_on_profile_name',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           side_effect=[[Mock(), Mock()], [Mock()]])
    def test_select_required_number_of_nodes_for_profile__sleep_until_time(self, *_):
        synced_nodes = self.flow.select_required_number_of_nodes_for_profile(self.user, "time")
        self.assertEqual(1, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_nodes_based_on_profile_name',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[Mock()])
    def test_select_required_number_of_nodes_for_profile__no_sleep(self, *_):
        synced_nodes = self.flow.select_required_number_of_nodes_for_profile(self.user, "no_sleep")
        self.assertEqual(1, len(synced_nodes))

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_nodes_based_on_profile_name')
    def test_select_required_number_of_nodes_for_profile__add_error_as_exception(self, mock_nodes, mock_error, *_):
        mock_nodes.returned_value = []
        self.flow.select_required_number_of_nodes_for_profile(self.user, "time")
        self.assertEqual(2, mock_nodes.call_count)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.node_pool_mgr.filter_unsynchronised_nodes',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.ShmFlow.select_nodes_based_on_profile_name')
    def test_select_required_number_of_nodes_for_profile__raises_EnmApplicationError(self, mock_nodes, mock_error, *_):
        mock_nodes.returned_value = []
        mock_nodes.side_effect = EnmApplicationError
        self.assertRaises(EnmApplicationError, self.flow.select_required_number_of_nodes_for_profile, self.user, "time")
        self.assertEqual(2, mock_nodes.call_count)
        self.assertTrue(mock_error.called)

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    def test_convert_time_string_to_datetime_object__success(self, mock_log, mock_datetime):
        mock_datetime.now.return_value = datetime(2021, 3, 22, 2, 0, 0, 0)
        self.flow.convert_time_string_to_datetime_object(["03:00:00"])
        mock_log.assert_any_call("SHM_JOB_SCHEDULED_TIME_STRINGS is [datetime.datetime(2021, 3, 22, 3, 0)]")

    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.datetime.datetime')
    @patch('enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger.debug')
    def test_convert_time_string_to_datetime_object__if_empty_str_passed(self, mock_log, mock_datetime):
        mock_datetime.now.return_value = datetime(2021, 3, 22, 2, 0, 0, 0)
        new_datetime = self.flow.convert_time_string_to_datetime_object([])
        mock_log.assert_any_call("SHM_JOB_SCHEDULED_TIME_STRINGS is []")
        self.assertEqual(new_datetime, [])

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger")
    def test_check_and_update_pib_values_for_backups__does_not_call_pib_for_other_deployments(self, mock_log,
                                                                                              mock_dep_config,
                                                                                              mock_get_pib, _):
        mock_dep_config.return_value = "forty_network"
        self.flow.check_and_update_pib_values_for_backups()
        self.assertTrue(mock_log.debug.call_count, 1)
        self.assertFalse(mock_get_pib.called)

    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger")
    def test_check_and_update_pib_values_for_backups__calls_error_log_when_exception_is_raised(self, mock_log,
                                                                                               mock_dep_config,
                                                                                               mock_get_pib, _):
        mock_get_pib.side_effect = Exception
        mock_dep_config.return_value = "soem_five_network"
        self.assertRaises(EnvironError, self.flow.check_and_update_pib_values_for_backups)

    @patch(
        "enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger")
    def test_check_and_update_pib_values_for_backups__has_calls_as_expected_backup_value(self, mock_log,
                                                                                         mock_dep_config,
                                                                                         mock_get_pib, _):
        mock_get_pib.side_effect = ["2"]
        mock_dep_config.return_value = "five_network"
        self.flow.check_and_update_pib_values_for_backups()
        self.assertTrue(mock_get_pib.call_count, 1)
        self.assertTrue(mock_log.debug.call_count, 3)

    @patch(
        "enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.update_pib_parameter_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.deploymentinfomanager_adaptor.check_deployment_config")
    @patch("enmutils_int.lib.profile_flows.shm_flows.shm_flow.log.logger")
    def test_check_and_update_pib_values_for_backups__calls_update_when_needed(self, mock_log, mock_dep_config,
                                                                               mock_get_pib, mock_update_pib):
        mock_get_pib.side_effect = ["5", "2"]
        mock_dep_config.return_value = "extra_small_network"
        self.flow.check_and_update_pib_values_for_backups()
        self.assertTrue(mock_get_pib.call_count, 1)
        self.assertTrue(mock_update_pib.call_count, 1)
        self.assertTrue(mock_log.debug.call_count, 3)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
