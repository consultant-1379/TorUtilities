#!/usr/bin/env python
import os

import unittest2
from mock import patch, Mock, PropertyMock, mock_open

from enmutils.lib.exceptions import CMImportError
from enmutils_int.lib.cm_import import CmImportLive
from enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile import (CmImportFlowProfile,
                                                                                 SimplifiedParallelCmImportFlow,
                                                                                 FILE_BASE_LOCATION,
                                                                                 CmImportSetupObject, EnvironWarning,
                                                                                 ReparentingCmImportFlow,
                                                                                 CmImport23Flow)
from testslib import unit_test_utils


class CmImportFlowProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.nodes = [Mock(), Mock()]
        self.user = Mock()

        flow_profile = CmImportFlowProfile()
        flow_profile.NAME = 'CMIMPORT_00'
        flow_profile.USER_ROLES = 'Cmedit_administrator'
        flow_profile.MO_VALUES = {'EUtranCellRelation': 5}
        flow_profile.TOTAL_NODES = 5
        flow_profile.FLOW = 'live_config'
        flow_profile.FILETYPE = 'dynamic'
        flow_profile.INTERFACE = 'NBIv2'
        flow_profile.IMPORT_TYPE = 'CreateDeleteLive'
        flow_profile.TIMEOUT = 0.001
        flow_profile.NUM_ITERATIONS = 1
        self.flow_profile = flow_profile

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_run(self):
        self.flow_profile.run()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_human_readable_timestamp')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportSetupObject')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.nodes_list',
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_total_num_mo_changes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.create_users')
    def test_setup_flow__is_successful(self, mock_create_users, mock_get_total_num_mo_changes, *_):
        self.flow_profile.setup_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_get_total_num_mo_changes.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_human_readable_timestamp')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportSetupObject')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.nodes_list',
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_total_num_mo_changes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.create_users')
    def test_setup_flow__is_successful_for_cmimport_26(self, mock_create_users, mock_get_total_num_mo_changes, *_):
        self.flow_profile.NAME = "CMIMPORT_26"
        self.flow_profile.setup_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_get_total_num_mo_changes.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_human_readable_timestamp')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.update_cm_ddp_info_log_entry')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportSetupObject')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_total_num_mo_changes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.nodes_list',
           new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.create_users')
    def test_setup_flow__is_successful_with_nodes_and_users_passed(self, mock_create_users, mock_nodes_list, *_):
        node, node1 = Mock(), Mock()
        setattr(node, 'node_version', '1-17')
        setattr(node1, 'node_version', '1-1')
        self.flow_profile.setup_flow(user=Mock(), nodes=[node, node1])
        self.assertEqual(mock_create_users.call_count, 0)
        self.assertEqual(mock_nodes_list.call_count, 0)

    def test_cmimport_create_delete_live_objects_is_successful(self):
        mock_setup_obj = Mock()
        mock_setup_obj.user = self.user
        mock_setup_obj.nodes = self.nodes
        mock_setup_obj.expected_num_mo_changes = 10
        with patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportDeleteLive') as mock_delete_live:
            with patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportCreateLive') as mock_create_live:
                self.flow_profile.cmimport_create_delete_live_objects(mock_setup_obj, 'cmimport_00', 'NBIv2', '.txt', 1)
                mock_delete_live.assert_called_with(name='cmimport_00_delete',
                                                    user=self.user,
                                                    nodes=self.nodes,
                                                    template_name='cmimport_00_delete.txt',
                                                    flow='live_config',
                                                    file_type='dynamic',
                                                    interface='NBIv2',
                                                    expected_num_mo_changes=10,
                                                    error_handling=None,
                                                    timeout=1)
                mock_create_live.assert_called_with(name='cmimport_00_create',
                                                    user=self.user,
                                                    nodes=self.nodes,
                                                    template_name='cmimport_00_create.txt',
                                                    flow='live_config',
                                                    file_type='dynamic',
                                                    interface='NBIv2',
                                                    expected_num_mo_changes=10,
                                                    error_handling=None,
                                                    timeout=1)

    def test_cmimport_update_live_objects_is_successful(self):
        mock_setup_obj = Mock()
        mock_setup_obj.user = self.user
        mock_setup_obj.nodes = self.nodes
        mock_setup_obj.expected_num_mo_changes = 10
        self.flow_profile.MOS_DEFAULT = {'TermPointToENB': ('administrativeState', 'LOCKED')}
        self.flow_profile.MOS_MODIFY = {'TermPointToENB': ('administrativeState', 'UNLOCKED')}

        with patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportUpdateLive') as mock_update_live:
            self.flow_profile.cmimport_update_live_objects(mock_setup_obj, 'cmimport_00', 'NBIv2', '.txt', 1)
            mock_update_live.assert_called_with(name='cmimport_00_modify',
                                                mos={'TermPointToENB': ('administrativeState', 'UNLOCKED')},
                                                user=self.user, nodes=self.nodes,
                                                template_name='cmimport_00_modify.txt', flow='live_config',
                                                file_type='dynamic', interface='NBIv2', error_handling=None,
                                                expected_num_mo_changes=10, timeout=1)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'cmimport_update_live_objects')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'cmimport_create_delete_live_objects')
    def test_get_cmimport_objects_is_successful(self, mock_create_delete_live, mock_update_live):
        self.flow_profile.IMPORT_TYPE = 'CreateDeleteLive'
        self.flow_profile.get_cmimport_objects(Mock())
        self.assertTrue(mock_create_delete_live.called)
        self.flow_profile.IMPORT_TYPE = 'UpdateLive'
        self.flow_profile.get_cmimport_objects(Mock())
        self.assertTrue(mock_update_live.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.keep_running',
           side_effect=[True, False])
    @ patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.retry_initial_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.initial_setup')
    def test_execute_cmimport_common_flow__is_successful(self, mock_setup, *_):
        context_mgr = Mock()
        mock_setup.return_value = context_mgr, Mock(), Mock()
        self.flow_profile.execute_cmimport_common_flow()
        self.assertTrue(context_mgr.run_import.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.keep_running',
           side_effect=[True, False])
    @ patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.retry_initial_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.initial_setup')
    def test_cmimport_common_flow__is_successful_cmimport_01(self, mock_setup, mock_sleep, *_):
        context_mgr = Mock()
        self.flow_profile.NAME = 'CMIMPORT_01'
        mock_setup.return_value = context_mgr, Mock(), Mock()
        self.flow_profile.execute_cmimport_common_flow()
        self.assertTrue(context_mgr.run_import.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.retry_initial_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.initial_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.'
           'add_error_as_exception')
    def test_cmimport_common_flow__adds_error_as_exception(self, mock_add_error, mock_setup, *_):
        context_mgr = Mock()
        mock_setup.return_value = context_mgr, False, Mock()
        context_mgr.run_import.side_effect = CMImportError
        self.flow_profile.teardown_list = Mock()
        self.flow_profile.execute_cmimport_common_flow()
        self.assertEqual(mock_add_error.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.retry_initial_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.initial_setup')
    def test_execute_cmimport_common_flow__successful_retry(self, mock_setup, mock_retry, *_):
        self.flow_profile.NAME = 'CMIMPORT_12'
        context_mgr = Mock()
        mock_setup.return_value = context_mgr, Mock(), Mock()
        mock_retry.return_value = Mock(), Mock(), Mock()
        setattr(context_mgr, 'setup_completed', False)
        self.flow_profile.execute_cmimport_common_flow()
        self.assertTrue(mock_retry.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ImportProfileContextManager')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.setup_flow')
    @patch(
        'enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.get_cmimport_objects')
    def test_initial_setup__success(self, mock_get_cmimport_objects, mock_setup_obj, _):
        mock_get_cmimport_objects.return_value = Mock(), Mock()
        self.flow_profile.initial_setup()
        self.assertTrue(mock_setup_obj.called)
        self.assertTrue(mock_get_cmimport_objects.called)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.setup')
    def test_retry_initial_setup__is_successful(self, mock_retry, mock_log, *_):
        context_mgr = Mock()
        mock_retry.return_value = context_mgr, Mock(), Mock(), True
        self.flow_profile.retry_initial_setup(Mock())
        self.assertEqual(1, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.initial_setup')
    def test_setup__success(self, mock_setup, mock_log, *_):
        mock_setup.return_value = Mock(), Mock(), Mock()
        self.flow_profile.setup()
        self.assertEqual(3, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.exchange_nodes')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.initial_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportFlowProfile.setup', side_effect=[[Mock(), Mock(), Mock(), False], [Mock(), Mock(), Mock(), True]])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_retry_initial_setup__is_unsuccessful(self, mock_log, *_):
        self.flow_profile.retry_initial_setup(Mock())
        self.assertEqual(2, mock_log.call_count)


class SimplifiedParallelCmImportFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.simplified = SimplifiedParallelCmImportFlow()
        self.simplified.FLOW = "live_config"
        self.simplified.NAME = "CmImport_Test"
        self.simplified.INTERFACE = "NBIv2"
        self.simplified.ERROR_HANDLING = ['parallel', 'continue-on-error']
        self.simplified.MO_ATTRS = {"geranCellId": 0, "cSysType": "GSM900", "cgi": 0}
        self.simplified.MOS_PER_NODE = 2
        self.simplified.MO_ID_START_RANGE = 1
        self.simplified.TARGET_MO = "GeranCell"
        self.simplified.PARENT_MO = "GeranCellM"
        self.simplified.USER_ROLES = ["Test"]
        self.simplified.NODES_PER_JOB = 1
        self.simplified.CGI_ROOT_VALUE = "999-999-9999"
        self.operation = "create"
        self.timestamp = "01-05-1111"
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'get_timestamp_str', return_value="0501")
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'get_parent_fdns', return_value=["FDN : ManagedElement=1"])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.common_utils.chunks')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_import_file')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_import_object')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_and_execute_threads')
    def test_execute_flow(self, mock_create_threads, mock_import_object, mock_import_file, mock_chunks, *_):
        mock_chunks.return_value = [[Mock()]]
        self.simplified.execute_flow()
        self.assertEqual(mock_create_threads.call_count, 1)
        self.assertEqual(mock_import_object.call_count, 2)
        self.assertEqual(mock_import_file.call_count, 2)
        mock_create_threads.assert_called_with([mock_import_object()], 1, args=[self.simplified])

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.state')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'get_timestamp_str', return_value="0501")
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'get_parent_fdns', return_value=[])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.common_utils.chunks')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_import_file')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_import_object')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'create_and_execute_threads')
    def test_execute_flow_no_parent_mos(self, mock_create_threads, mock_import_object, mock_import_file, mock_chunks,
                                        *_):
        node = Mock()
        node.node_id = "BSC01"
        mock_chunks.return_value = [[node]]
        self.simplified.execute_flow()
        self.assertEqual(mock_create_threads.call_count, 0)
        self.assertEqual(mock_import_object.call_count, 0)
        self.assertEqual(mock_import_file.call_count, 0)

    def test_get_parent_fdns(self):
        response = Mock()
        response.get_output.return_value = [u'FDN : ManagedElement=1', u'FDN : ManagedElement=1', u'ManagElement']
        self.user.enm_execute.return_value = response
        node = Mock()
        node.node_id = "LTE01"
        fdns = self.simplified.get_parent_fdns(self.user, [node])
        self.assertEqual(2, len(fdns))

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow.'
           'add_error_as_exception')
    def test_get_parent_fdns_adds_error(self, mock_add_error):
        self.user.enm_execute.side_effect = Exception("Error")
        node = Mock()
        node.node_id = "LTE01"
        self.simplified.get_parent_fdns(self.user, [node])
        self.assertEqual(1, mock_add_error.call_count)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow'
           '.write_attributes_file')
    def test_create_import_file(self, mock_write_attributes, mock_file_open):
        parent_fdns = ["FDN : ManageElement=1,GeranCellM"]
        self.simplified.create_import_file(parent_fdns, self.operation, self.timestamp)
        expected = "{0}.txt".format(os.path.join(FILE_BASE_LOCATION, "{0}_{1}_{2}".format(
            self.simplified.NAME.lower(), "create", self.timestamp)))
        self.assertEqual(expected, self.simplified.file_path)
        self.assertEqual(2, mock_file_open.return_value.write.call_count)
        self.assertEqual(2, mock_write_attributes.call_count)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.SimplifiedParallelCmImportFlow'
           '.write_attributes_file')
    def test_create_import_file_does_not_write_attributes_if_delete_operation(self, mock_write_attributes, *_):
        parent_fdns = ["FDN : ManageElement=1,GeranCellM"]
        self.simplified.create_import_file(parent_fdns, "delete", self.timestamp)
        expected = "{0}.txt".format(os.path.join(FILE_BASE_LOCATION, "{0}_{1}_{2}".format(
            self.simplified.NAME.lower(), "delete", self.timestamp)))
        self.assertEqual(expected, self.simplified.file_path)
        self.assertEqual(0, mock_write_attributes.call_count)

    @patch('enmutils.lib.log.logger.debug')
    def test_write_attributes_file__success(self, mock_debug):
        self.simplified.CGI_VALUES = ["1", "2", "3", "4"]
        file_obj = Mock()
        self.simplified.write_attributes_file(file_obj, 1)
        mock_debug.assert_called_with("Successfully wrote attribute to import file.")
        self.assertEqual(3, file_obj.write.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.get_human_readable_timestamp')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.update_cm_ddp_info_log_entry')
    @patch('enmutils.lib.log.logger.debug')
    def test_create_import_object__success(self, mock_debug, *_):
        user = Mock()
        nodes = [Mock()]

        import_object = self.simplified.create_import_object(user, nodes, self.operation, self.timestamp)
        mock_debug.assert_called_with('Created cmimport objects for profile: {0}, for operation {1}'
                                      .format(self.simplified.NAME.lower(), self.operation))
        self.assertTrue(isinstance(import_object, CmImportLive))

    def test_task_set__adds_error(self):
        error = Exception("Error")
        worker = Mock()
        worker.import_flow.side_effect = error
        profile = Mock()
        self.simplified.task_set(worker, profile)
        profile.add_error_as_exception.assert_called_with(error)


class CmImportSetupObjectUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test__init___is_successful(self):
        nodes = ['node_1']
        expected_num_mo_changes = 1
        cmimport_setup_object = CmImportSetupObject(nodes, self.user, expected_num_mo_changes)
        self.assertEqual(cmimport_setup_object.nodes, nodes)
        self.assertEqual(cmimport_setup_object.user, self.user)
        self.assertEqual(cmimport_setup_object.expected_num_mo_changes, expected_num_mo_changes)

    def test_cmimport_setup_object__coverage(self):
        setup = CmImportSetupObject("", "", 10)
        self.assertEqual(10, setup.expected_num_mo_changes)


class ReparentingCmImportFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = ReparentingCmImportFlow()
        self.flow.teardown_list = []

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.persistence.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'state', new_callable=PropertyMock, return_value="RUNNING")
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'get_required_bsc')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.copy_files')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'create_import_object')
    def test_execute_flow__success(self, mock_import, *_):
        self.flow.execute_flow()
        self.assertEqual(2, mock_import.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'state', new_callable=PropertyMock, return_value="RUNNING")
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.copy_files')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'get_required_bsc', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.keep_running')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'add_error_as_exception')
    def test_execute_flow__setup_fails(self, mock_add_error, mock_keep, *_):
        self.flow.execute_flow()
        self.assertEqual(0, mock_keep.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.persistence.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'state', new_callable=PropertyMock, return_value="RUNNING")
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'get_required_bsc')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.copy_files')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'create_import_object')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.ReparentingCmImportFlow.'
           'add_error_as_exception')
    def test_execute_flow__adds_error(self, mock_add_error, mock_import, *_):
        mock_import.return_value.import_flow.side_effect = Exception("Error")
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_get_required_bsc__success(self, mock_debug):
        user, response = Mock(), Mock()
        response.get_output.return_value = [u'', u'1 instance(s)']
        user.enm_execute.return_value = response
        self.flow.get_required_bsc(user, 'ID')
        mock_debug.assert_called_with("Completed querying ENM for node:: ID.")

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_get_required_bsc__raises_environ_warning(self, _):
        user, response = Mock(), Mock()
        response.get_output.return_value = [u'', u'0 instance(s)']
        user.enm_execute.return_value = response
        self.assertRaises(EnvironWarning, self.flow.get_required_bsc, user, '')

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.pkgutil.get_loader')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.unipath.Path')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.filesystem.copy')
    def test_copy_files__success(self, mock_copy, *_):
        self.flow.copy_files()
        self.assertEqual(2, mock_copy.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportLive.__init__',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_create_import_object__success(self, mock_debug, _):
        self.flow.create_import_object('', 'create', 'test.txt')
        mock_debug.assert_called_with('Created cmimport objects for profile: reparentingcmimportflow, for '
                                      'operation create.')


class CmImport23FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CmImport23Flow()
        self.flow.teardown_list = []
        self.flow.MOS_PER_NODE = 2
        self.flow.FLOW = 'live_config'
        self.flow.FILETYPE = 'dynamic'
        self.flow.USER_ROLES = 'Cmedit_Administrator'
        self.user = Mock()
        self.nodes = [Mock(), Mock()]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.'
           'get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.'
           'state', new_callable=PropertyMock, return_value="RUNNING")
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.'
           'sleep_until_next_scheduled_iteration')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.flow_setup')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.'
           'create_delete_obj')
    def test_execute_flow__success(self, mock_import, mock_flow_setup, *_):
        mock_flow_setup.return_value = 'create.txt', 'delete.txt'
        self.flow.execute_flow()
        self.assertEqual(1, mock_import.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.persistence.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.create_import_object')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.create_file')
    def test_flow_setup__success(self, mock_create_file, mock_log, *_):
        self.flow.flow_setup(self.user, self.nodes)
        self.assertEqual(2, mock_create_file.call_count)
        self.assertEqual(2, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.create_import_object')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_create_delete_obj__success(self, mock_log, *_):
        file_path = Mock()
        self.flow.create_delete_obj(self.user, self.nodes, file_path, file_path)
        self.assertEqual(2, mock_log.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.create_import_object')
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImport23Flow.add_error_as_exception')
    def test_create_delete_obj__adds_error(self, mock_add_error, mock_import, *_):
        mock_import.return_value.import_flow.side_effect = Exception("Error")
        file_path = Mock()
        self.flow.create_delete_obj(self.user, self.nodes, file_path, file_path)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.CmImportLive.__init__',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_create_import_object__success(self, mock_debug, _):
        self.flow.create_import_object(self.user, self.nodes, 'create', 'test.txt')
        mock_debug.assert_called_with('Created cmimport object for profile: cmimport23flow, for operation create.')

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_create_file__success(self, mock_log, mock_open_file):
        file_path = Mock()
        cmd = Mock()
        node = Mock()
        node.node_id = ['epgoi_node']
        self.flow.create_file(file_path, cmd, self.nodes)
        self.assertEqual(4, mock_open_file.return_value.write.call_count)
        self.assertEqual(2, mock_log.call_count)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_create_file__raises_exception(self, mock_log, mock_open_file):
        file_path = Mock()
        cmd = Mock()
        node = Mock()
        node.node_id = ['epgoi_node']
        mock_open_file.side_effect = Exception
        self.flow.create_file(file_path, cmd, self.nodes)
        self.assertEqual(2, mock_log.call_count)

    @patch('__builtin__.open', new_callable=mock_open)
    @patch('enmutils_int.lib.profile_flows.cmimport_flows.cmimport_flow_profile.log.logger.debug')
    def test_create_file__raises_exception_if_no_nodes(self, mock_log, _):
        file_path = Mock()
        cmd = Mock()
        node = Mock()
        self.flow.create_file(file_path, cmd, node)
        self.assertEqual(2, mock_log.call_count)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
