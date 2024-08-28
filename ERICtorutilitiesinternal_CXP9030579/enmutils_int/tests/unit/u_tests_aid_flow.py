#!/usr/bin/env python
import datetime

import unittest2
from mock import patch, Mock, PropertyMock, call
from requests.exceptions import HTTPError
from enmutils_int.lib.nrm_default_configurations.forty_network import forty_k_network
from enmutils_int.lib.profile_flows.aid_flows.aid_flow import (Aid01Flow, Aid02Flow, Aid03Flow, Aid04Flow,
                                                               parallel_executions, EnmApplicationError,
                                                               _wait_for_setup_profile)
from enmutils_int.lib.load_node import ERBSLoadNode, RadioLoadNode
from enmutils_int.lib.workload import aid_01, aid_02, aid_03, aid_04
from testslib import unit_test_utils


class Aid01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.aid_01 = aid_01.AID_01()
        self.flow = Aid01Flow()
        self.flow.NUM_USERS = 10
        self.flow.USER_ROLES = ['AutoId_Administrator']
        self.flow.AID_PROFILE_SLEEP = 30
        self.flow.SCHEDULED_TIMES_STRINGS = ['00:15:00', '01:15:00', '02:15:00', '03:15:00', '04:15:00',
                                             '05:15:00', '06:15:00', '07:15:00', '08:15:00', '09:15:00',
                                             '10:15:00', '11:15:00', '12:15:00', '13:15:00', '14:15:00',
                                             '15:15:00', '16:15:00', '17:15:00', '18:15:00', '19:15:00',
                                             '20:15:00', '21:15:00', '22:15:00', '23:15:00']
        self.nodes = [ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERBS00004',
                                   simulation='LTE-120', model_identity='1-2-34', primary_type='ERBS',
                                   poid='181477779762365'),
                      ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERS00020',
                                   simulation='LTE-UPGIND-120', model_identity='1-2-34', primary_type='ERBS',
                                   poid='181477479762365'),
                      RadioLoadNode(node_id='LTEDG201', id='LTEDG201', simulation='LTEDG2-120',
                                    model_identity='1-2-35', primary_type='RadioNode',
                                    poid='181477379762365'),
                      RadioLoadNode(node_id='LTEDG202', id='LTEDG202', simulation='LTE-DG2M-120',
                                    model_identity='1-2-36', primary_type='RadioNode', poid='181477779762865')]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.execute_flow')
    def test_run__in_aid_01_is_successful(self, mock_execute_flow):
        self.aid_01.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.parallel_executions')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.identifier', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.create_users')
    def test_execute_flow__is_successfully_executed(self, mock_create_users, mock_nodes_list, mock_collection,
                                                    mock_identifier, mock_parallel_executions, *_):
        with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.'
                   'create_and_execute_threads') as mock_create_and_execute_threads:
            with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.'
                       'Aid01Flow.keep_running') as mock_keep_running:
                with patch('enmutils_int.lib.profile.TeardownList.append') as mock_teardown_append:
                    with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile',
                               return_value=True):
                        users = [self.user for _ in xrange(10)]
                        identifier = Mock()
                        collection = Mock()
                        mock_create_users.return_value = users
                        mock_nodes_list.return_value = self.nodes
                        mock_keep_running.side_effect = [True, False]

                        mock_collection.return_value = collection
                        mock_identifier.return_value = identifier
                        self.flow.execute_flow()

                        mock_create_and_execute_threads.assert_called_with(workers=users, thread_count=len(users),
                                                                           func_ref=mock_parallel_executions,
                                                                           args=[collection, identifier, 2, self.flow],
                                                                           wait=60 * 60, join=5 * 60)
                        self.assertEqual(mock_create_and_execute_threads.call_count, 3)
                        self.assertTrue(mock_create_users.called)
                        self.assertTrue(mock_keep_running.called)
                        self.assertTrue(mock_teardown_append.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=False)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.create_users')
    def test_execute_flow__no_run_if_setup_profile_in_error_state(self, mock_create_users, mock_nodes_list,
                                                                  mock_collection, mock_keep_running,
                                                                  mock_add_error_as_exception, *_):
        mock_collection.return_value.create.side_effect = Exception
        mock_nodes_list.return_value = self.nodes
        self.flow.execute_flow()
        self.assertFalse(mock_create_users.called)
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertFalse(mock_keep_running.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.create_users')
    def test_execute_flow__raises_exception_if_collection_cannot_be_created(self, mock_create_users, mock_nodes_list,
                                                                            mock_collection, mock_keep_running,
                                                                            mock_add_error_as_exception, *_):
        mock_collection.return_value.create.side_effect = Exception
        mock_nodes_list.return_value = self.nodes
        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertFalse(mock_keep_running.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.NonPlannedPCIRange')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.TopologyGroupRange')
    def test_parallel_executions__is_successfully_executed(self, mock_topology, mock_non_planned, mock_manual_aid,
                                                           mock_collection, mock_add_error_as_exception, *_):
        with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug') as mock_debug_log:
            mock_list = [mock_manual_aid, mock_topology, mock_non_planned]
            self.user.open_session = Mock()
            self.flow.add_error_as_exception = Mock()
            for loop in xrange(3):
                parallel_executions(self.user, mock_collection, self.flow.identifier, loop, self.flow)
                self.assertTrue(mock_list[loop].called)
            self.assertFalse(mock_add_error_as_exception.called)
            self.assertEqual(mock_debug_log.call_count, 12)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    def test_parallel_executions__raises_exception_while_deleting_the_manual_autoid_profile(self, mock_manual_aid,
                                                                                            mock_collection,
                                                                                            mock_add_error_as_exception,
                                                                                            *_):
        with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug') as mock_debug_log:
            self.user.open_session = Mock()
            mock_manual_aid.return_value.delete.side_effect = Exception("something is wrong")
            parallel_executions(self.user, mock_collection, self.flow.identifier, 0, self.flow)
            self.assertTrue(mock_manual_aid.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertEqual(mock_debug_log.call_count, 6)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.TopologyGroupRange')
    def test_parallel_executions__raises_exception_while_deleting_the_topology_group_range(self, mock_topology,
                                                                                           mock_collection,
                                                                                           mock_add_error_as_exception,
                                                                                           *_):
        with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug') as mock_debug_log:
            self.user.open_session = Mock()
            mock_topology.return_value.delete.side_effect = Exception("something is wrong")
            parallel_executions(self.user, mock_collection, self.flow.identifier, 1, self.flow)
            self.assertTrue(mock_topology.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertEqual(mock_debug_log.call_count, 6)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.NonPlannedPCIRange')
    def test_parallel_executions__raises_exception_while_deleting_the_non_planned_pci_range(self, mock_non_planned,
                                                                                            mock_collection,
                                                                                            mock_add_error_as_exception,
                                                                                            *_):
        with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug') as mock_debug_log:
            self.user.open_session = Mock()
            mock_non_planned.return_value.delete.side_effect = Exception("something is wrong")
            parallel_executions(self.user, mock_collection, self.flow.identifier, 2, self.flow)
            self.assertTrue(mock_non_planned.called)
            self.assertTrue(mock_add_error_as_exception.called)
            self.assertEqual(mock_debug_log.call_count, 6)


class Aid02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.aid_02 = aid_02.AID_02()
        self.flow = Aid02Flow()
        self.flow.AID_PROFILE_TIMEOUT = 10800
        self.flow.add_error_as_exception = Mock()
        aid_02_settings = forty_k_network["forty_k_network"]["aid"]
        for key, value in aid_02_settings['AID_02'].items():
            setattr(self.flow, key, value)
        self.nodes = [ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERBS00004',
                                   simulation='LTE-120', model_identity='1-2-34', primary_type='ERBS',
                                   poid='181477779762365'),
                      ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERS00020',
                                   simulation='LTE-UPGIND-120', model_identity='1-2-34', primary_type='ERBS',
                                   poid='181477479762365'),
                      RadioLoadNode(node_id='LTEDG201', id='LTEDG201', simulation='LTEDG2-120',
                                    model_identity='1-2-35', primary_type='RadioNode',
                                    poid='181477379762365'),
                      RadioLoadNode(node_id='LTEDG202', id='LTEDG202', simulation='LTE-DG2M-120',
                                    model_identity='1-2-36', primary_type='RadioNode', poid='181477779762865')]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.execute_flow')
    def test_run__in_aid_02_is_successful(self, mock_execute_flow):
        self.aid_02.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.AutoIdTearDownProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.create_profile_users')
    def test_execute_flow__is_successfully_executed(self, mock_create_profile_users, mock_annotate_fdn,
                                                    mock_keep_running, mock_manual_aid_profile, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_aid_profile = Mock()
        mock_aid_profile.exceptions = []
        mock_annotate_fdn.return_value = self.nodes
        mock_keep_running.side_effect = [True, False]
        mock_manual_aid_profile.return_value = mock_aid_profile
        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_annotate_fdn.called)
        self.assertTrue(mock_keep_running.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=False)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.AutoIdTearDownProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.create_profile_users')
    def test_execute_flow__no_run_when_wait_for_setup_profile_errors(self, mock_create_profile_users, mock_annotate_fdn,
                                                                     mock_keep_running, mock_manual_aid_profile, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_aid_profile = Mock()
        mock_aid_profile.exceptions = []
        mock_annotate_fdn.return_value = self.nodes
        mock_keep_running.side_effect = [True, False]
        mock_manual_aid_profile.return_value = mock_aid_profile
        self.flow.execute_flow()
        self.assertFalse(mock_create_profile_users.called)
        self.assertFalse(mock_annotate_fdn.called)
        self.assertFalse(mock_keep_running.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.AutoIdTearDownProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.create_profile_users')
    def test_execute_flow__fails_in_finding_node_objects(self, mock_create_profile_users, mock_annotate_fdn,
                                                         mock_keep_running, mock_manual_aid_profile, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_annotate_fdn.side_effect = HTTPError
        self.flow.execute_flow()
        self.assertFalse(mock_keep_running.called)
        self.assertFalse(mock_manual_aid_profile.called)
        self.assertTrue(self.flow.add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.AutoIdTearDownProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.create_profile_users')
    def test_execute_flow__fails_in_creating_aid_objects(self, mock_create_profile_users, mock_annotate_fdn,
                                                         mock_keep_running, mock_manual_aid_profile, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_aid_profile = Mock()
        mock_aid_profile.exceptions = []
        mock_aid_profile.create.side_effect = Exception
        mock_annotate_fdn.return_value = self.nodes
        mock_manual_aid_profile.side_effect = [mock_aid_profile, Exception]
        self.flow.execute_flow()
        self.assertFalse(mock_keep_running.called)
        self.assertTrue(self.flow.add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.AutoIdTearDownProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ManualAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid02Flow.create_profile_users')
    def test_execute_flow__fails_in_profile_calculate(self, mock_create_profile_users, mock_annotate_fdn,
                                                      mock_keep_running, mock_manual_aid_profile, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_aid_profile = Mock()
        mock_aid_profile.calculate.side_effect = Exception
        mock_aid_profile.exceptions = [Exception]

        mock_annotate_fdn.return_value = self.nodes
        mock_keep_running.side_effect = [True, False]
        mock_manual_aid_profile.return_value = mock_aid_profile
        self.flow.execute_flow()
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_annotate_fdn.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(self.flow.add_error_as_exception.called)


class Aid04FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.aid_04 = aid_04.AID_04()
        self.flow = Aid04Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['AutoId_Administrator', "ADMINISTRATOR"]
        self.flow.SCHEDULED_TIMES_STRINGS = ['02:00:00']
        self.flow.MO_BATCH_SIZE = 2
        self.flow.BATCH_MO_SIZE = 2
        self.flow.NODES_PER_HOST = 1
        self.flow.MO_ATTRIBUTE_DATA = {'EUtranCellFDD': [['physicalLayerCellIdGroup', 0, 167],
                                                         ['physicalLayerSubCellId', 0, 2]]}
        self.flow.MO_VALUES = {'EUtranCellFDD': 1}
        self.flow.RUN_TYPE = 'NEW'
        self.flow.NUM_NODES_PER_BATCH = 2
        self.flow.EXCLUDE_NODE_VERSIONS = ['18.Q3', '18.Q4']
        self.flow.teardown_list = []

        self.nodes_list = [
            ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERBS00004', simulation='LTE-120',
                         model_identity='1-2-34', primary_type='ERBS', poid='181477779763365'),
            ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERS00020', simulation='LTE-UPGIND-120',
                         model_identity='1-2-34', primary_type='ERBS', poid='181477779763366'),
            RadioLoadNode(node_id='LTEDG201', id='LTEDG201', simulation='LTEDG2-120', model_identity='1-2-35',
                          primary_type='RadioNode', poid='181477779763466'),
            RadioLoadNode(node_id='LTEDG202', id='LTEDG202', simulation='LTE-DG2M-120', model_identity='1-2-36',
                          primary_type='RadioNode', poid='181577779763466')]

        self.node_cell_data = {
            'netsim_LTE02ERBS00004': {u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,'
                                      u'MeContext=netsim_LTE02ERBS00004,ManagedElement=1,ENodeBFunction=1,'
                                      u'EUtranCellFDD=LTE02ERBS00004-1': {'DEFAULT': {'physicalLayerSubCellId': '0',
                                                                                      'physicalLayerCellIdGroup': '0'},
                                                                          'NEW': {'physicalLayerSubCellId': 0,
                                                                                  'physicalLayerCellIdGroup': 0}}},
            'netsim_LTE02ERS00020': {u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=ERBS-SUBNW-1,'
                                     u'MeContext=netsim_LTE02ERBS00020,ManagedElement=1,ENodeBFunction=1,'
                                     u'EUtranCellFDD=LTE02ERBS00020-7': {'DEFAULT': {'physicalLayerSubCellId': '0',
                                                                                     'physicalLayerCellIdGroup': '0'},
                                                                         'NEW': {'physicalLayerSubCellId': 0,
                                                                                 'physicalLayerCellIdGroup': 0}}}}
        self.nodes_for_injection = [self.nodes_list[0], self.nodes_list[1]]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.execute_flow')
    def test_run__in_aid_04_is_successful(self, mock_execute_flow):
        self.aid_04.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.update_cells_attributes_via_netsim')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.create')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_node_cell_data')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__success(self, mock_node_objects, mock_cell_data, mock_create, mock_update, *_):
        mock_node_objects.return_value = [Mock(lte_cell_type="FDD"), Mock(lte_cell_type="TDD")]
        self.flow.execute_flow()
        self.assertEqual(1, mock_cell_data.call_count)
        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(1, mock_update.call_count)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=False)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.update_cells_attributes_via_netsim')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.create')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_node_cell_data')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__no_run_wait_for_setup_profile_errors(self, mock_node_objects, mock_cell_data, mock_create, mock_update, *_):
        mock_node_objects.return_value = [Mock(lte_cell_type="FDD"), Mock(lte_cell_type="TDD")]
        self.flow.execute_flow()
        self.assertEqual(0, mock_cell_data.call_count)
        self.assertEqual(0, mock_create.call_count)
        self.assertEqual(0, mock_update.call_count)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.update_cells_attributes_via_netsim')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.create')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_node_cell_data')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__no_verified_nodes(self, mock_node_objects, mock_cell_data, mock_create, mock_update,
                                             mock_add_error, *_):
        mock_node_objects.side_effect = Exception("Some error")
        self.flow.execute_flow()
        self.assertEqual(0, mock_cell_data.call_count)
        self.assertEqual(0, mock_create.call_count)
        self.assertEqual(0, mock_update.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.update_cells_attributes_via_netsim')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.create',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_node_cell_data')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__aid_profile_create_fails(self, mock_node_objects, mock_cell_data, mock_create, mock_update,
                                                    mock_add_error, *_):
        mock_node_objects.return_value = [Mock(lte_cell_type="FDD"), Mock(lte_cell_type="TDD")]
        self.flow.execute_flow()
        self.assertEqual(1, mock_cell_data.call_count)
        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(0, mock_update.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.state', new_callable=PropertyMock,
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.update_cells_attributes_via_netsim',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.ClosedLoopAutoIdProfile.create')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.get_node_cell_data')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__netsim_update_fails(self, mock_node_objects, mock_cell_data, mock_create, mock_update,
                                               mock_add_error, *_):
        mock_node_objects.return_value = [Mock(lte_cell_type="FDD"), Mock(lte_cell_type="TDD")]
        self.flow.execute_flow()
        self.assertEqual(1, mock_cell_data.call_count)
        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(1, mock_update.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.populate_node_cell_data')
    def test_get_node_cell_data__adds_multiple_cell_types(self, mock_populate_node_cell_data):
        mock_populate_node_cell_data.side_effect = [{"Key": "Value"}, {"Key1": "Value1"}]
        expected = {"Key": "Value", "Key1": "Value1"}
        self.assertDictEqual(expected, self.flow.get_node_cell_data(self.user,
                                                                    [[], [Mock(lte_cell_type="FDD")],
                                                                     [Mock(lte_cell_type="TDD")]]))
        self.assertEqual(2, mock_populate_node_cell_data.call_count)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.generate_node_batches')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.create_and_execute_threads')
    def test_update_cells_attributes_via_netsim__is_successfully_executed(self, mock_create_and_execute_threads,
                                                                          mock_generate_node_batches):
        mock_generate_node_batches.return_value = [[self.nodes_list[0]], self.nodes_list[1]]

        self.flow.update_cells_attributes_via_netsim(self.node_cell_data, self.nodes_for_injection)
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_generate_node_batches.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.get_cell_name')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.timestamp.get_current_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.execute_netsim_command_on_netsim_node')
    def test_set_aid_inconsistencies_on_nodes__is_successfully_executed(self, mock_execute_netsim_command,
                                                                        mock_get_current_time, mock_debug_log,
                                                                        mock_add_error, *_):
        mock_execute_netsim_command.return_value = True
        mock_get_current_time.return_value = datetime.datetime(2020, 1, 9, 0, 0, 0, 0)
        nodes = [self.nodes_list[0], self.nodes_list[1]]
        self.flow.set_aid_inconsistencies_on_nodes(nodes, self.flow, self.node_cell_data)
        self.assertTrue(mock_debug_log.call_count, 1)
        self.assertTrue(mock_execute_netsim_command.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.get_cell_name')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.timestamp.get_current_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.execute_netsim_command_on_netsim_node')
    def test_set_aid_inconsistencies_on_nodes__raises_exception(self, mock_execute_netsim_command,
                                                                mock_get_current_time, mock_debug_log, mock_add_error,
                                                                *_):
        mock_execute_netsim_command.side_effect = Exception()
        mock_get_current_time.return_value = datetime.datetime(2020, 1, 9, 0, 0, 0, 0)
        nodes = [self.nodes_list[0], self.nodes_list[1]]
        self.flow.set_aid_inconsistencies_on_nodes(nodes, self.flow, self.node_cell_data)
        self.assertTrue(mock_debug_log.called)
        self.assertTrue(mock_execute_netsim_command.called)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.get_cell_name')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.timestamp.get_current_time')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid04Flow.execute_netsim_command_on_netsim_node')
    def test_set_aid_inconsistencies_on_nodes__if_execute_netsim_command_returns_false(self,
                                                                                       mock_execute_netsim_command,
                                                                                       mock_get_current_time,
                                                                                       mock_debug_log, mock_add_error,
                                                                                       *_):
        mock_execute_netsim_command.return_value = False
        mock_get_current_time.return_value = datetime.datetime(2020, 1, 9, 0, 0, 0, 0)
        nodes = [self.nodes_list[0], self.nodes_list[1]]
        self.flow.set_aid_inconsistencies_on_nodes(nodes, self.flow, self.node_cell_data)
        self.assertEqual(mock_debug_log.call_count, 6)
        self.assertEqual(2, mock_execute_netsim_command.call_count)
        self.assertTrue(call(EnmApplicationError("Operation has encountered errors, "
                                                 "please check the logs for more information.") in
                             mock_add_error.mock_calls))


class Aid03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.aid_03 = aid_03.AID_03()
        self.flow = Aid03Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['AutoId_Administrator']
        self.EXCLUDE_NODES_FROM = ["AID_04"]

        self.nodes_list = [ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERBS00004',
                                        simulation='LTE-120', model_identity='1-2-34', primary_type='ERBS',
                                        poid='181477779762365'),
                           ERBSLoadNode(node_id='netsim_LTE02ERBS00004', id='netsim_LTE02ERS00020',
                                        simulation='LTE-UPGIND-120', model_identity='1-2-34', primary_type='ERBS',
                                        poid='181477479762365'),
                           RadioLoadNode(node_id='LTEDG201', id='LTEDG201', simulation='LTEDG2-120',
                                         model_identity='1-2-35', primary_type='RadioNode',
                                         poid='181477379762365'),
                           RadioLoadNode(node_id='LTEDG202', id='LTEDG202', simulation='LTE-DG2M-120',
                                         model_identity='1-2-36', primary_type='RadioNode', poid='181477779762865')]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.execute_flow')
    def test_run__in_aid_03_is_successful(self, mock_execute_flow):
        self.aid_03.run()
        self.assertTrue(mock_execute_flow.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.OpenLoopAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch("enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.create_users")
    def test_execute_flow__is_successfully_executed(self, mock_create_user, mock_annotate_fdn_poid,
                                                    mock_open_loop_profile, mock_nodes_list, *_):
        with patch("enmutils_int.lib.profile.TeardownList.append") as mock_teardown_append:
            mock_create_user.return_value = [self.user]
            mock_nodes_list.return_value = self.nodes_list
            mock_annotate_fdn_poid.return_value = mock_nodes_list

            mock_open_loop_profile_instance = Mock()
            mock_open_loop_profile_instance.create = Mock()
            mock_open_loop_profile.return_value = mock_open_loop_profile_instance

            self.flow.execute_flow()
            self.assertTrue(mock_annotate_fdn_poid.called)
            self.assertTrue(mock_open_loop_profile_instance.create.called)
            self.assertTrue(mock_create_user.called)
            self.assertTrue(mock_teardown_append.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=False)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.OpenLoopAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch("enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.create_users")
    def test_execute_flow__no_run_when_setup_profile_error(self, mock_create_user, mock_annotate_fdn_poid,
                                                           mock_open_loop_profile, mock_nodes_list, *_):
        with patch("enmutils_int.lib.profile.TeardownList.append") as mock_teardown_append:
            mock_create_user.return_value = [self.user]
            mock_nodes_list.return_value = self.nodes_list
            mock_annotate_fdn_poid.return_value = mock_nodes_list

            mock_open_loop_profile_instance = Mock()
            mock_open_loop_profile_instance.create = Mock()
            mock_open_loop_profile.return_value = mock_open_loop_profile_instance

            self.flow.execute_flow()
            self.assertFalse(mock_annotate_fdn_poid.called)
            self.assertFalse(mock_open_loop_profile_instance.create.called)
            self.assertFalse(mock_create_user.called)
            self.assertFalse(mock_teardown_append.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow._wait_for_setup_profile', return_value=True)
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.OpenLoopAutoIdProfile')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.annotate_fdn_poid_return_node_objects')
    @patch("enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.create_users")
    def test_execute_flow__raises_exception_when_open_loop_profile_created(self, mock_create_user,
                                                                           mock_annotate_fdn_poid,
                                                                           mock_open_loop_profile,
                                                                           mock_add_error_as_exception, *_):
        with patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.Aid03Flow.'
                   'get_nodes_list_by_attribute') as mock_nodes_list:
            with patch("enmutils_int.lib.profile.TeardownList.append") as mock_teardown_append:
                mock_create_user.return_value = [self.user]
                mock_nodes_list.return_value = self.nodes_list
                mock_annotate_fdn_poid.return_value = mock_nodes_list

                mock_open_loop_profile_instance = Mock()
                mock_open_loop_profile_instance.create = Mock()
                mock_open_loop_profile_instance.create.side_effect = Exception()
                mock_open_loop_profile.return_value = mock_open_loop_profile_instance

                self.flow.execute_flow()
                self.assertTrue(mock_add_error_as_exception.call_count, 1)
                self.assertTrue(mock_open_loop_profile_instance.create.called)
                self.assertFalse(mock_teardown_append.called)

    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.load_mgr.wait_for_setup_profile')
    def test__wait_for_setup_profile_successful(self, mock_wait_for_profile):
        _wait_for_setup_profile(self)
        self.assertTrue(mock_wait_for_profile.called)

    @patch('enmutils_int.lib.profile.Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.aid_flows.aid_flow.load_mgr.wait_for_setup_profile')
    def test__wait_for_setup_profile_adds_exception(self, mock_wait_for_profile, mock_add_error):
        mock_wait_for_profile.side_effect = Exception
        _wait_for_setup_profile(self.flow)
        self.assertTrue(mock_add_error.call_count is 1)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
