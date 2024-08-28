#!/usr/bin/env python
import time
from datetime import datetime

import unittest2
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.load_node import ERBSLoadNode, RadioLoadNode
from enmutils_int.lib.node_security import (NodeCredentials, NodeSecurityLevel, NodeSNMP, NodeCertificate,
                                            NodeTrust, SecurityConfig)
from enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow import (NodeSecFlow, NodeSec01Flow, NodeSec02Flow,
                                                                       NodeSec03Flow, NodeSec04Flow, NodeSec08Flow,
                                                                       NodeSec11Flow, NodeSec13Flow, NodeSec15Flow,
                                                                       NodeSec18Flow, picklable_boundmethod, partial)
from enmutils_int.lib.workload import (nodesec_01, nodesec_02, nodesec_03, nodesec_04, nodesec_08, nodesec_11,
                                       nodesec_13, nodesec_15, nodesec_18)
from mock import patch, Mock, PropertyMock, call, MagicMock
from testslib import unit_test_utils


class NodeSecFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = NodeSecFlow()
        self.nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34'),
                           ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34')]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.check_sync_and_remove')
    def test_get_synchronised_nodes_logs_unsynced(self, mock_check_sync_and_remove, mock_debug):
        mock_check_sync_and_remove.return_value = [], [Mock(), Mock()]
        self.flow.get_synchronised_nodes(self.nodes_list, self.user)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.load_mgr.wait_for_setup_profile')
    def test_wait_for_profile__called_wait_for_setup_profile(self, mock_wait_for_setup):
        self.flow.wait_for_profile(["15"])
        mock_wait_for_setup.assert_called_with(profile_name='NODESEC_03', state_to_wait_for='COMPLETED',
                                               timeout_mins=20)

    @patch('enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.add_error_as_exception')
    def test_create_and_execute_threads__add_error_if_no_workers(self, mock_add_error):
        self.flow.create_and_execute_threads([], 1)
        self.assertTrue(mock_add_error.called)


class NodeSec01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_01 = nodesec_01.NODESEC_01()
        self.flow = NodeSec01Flow()
        self.flow.NUM_BATCHES = 2
        self.nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34', primary_type='ERBS'),
                           ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34',
                                        primary_type='ERBS'),
                           RadioLoadNode(id='LTEDG201', simulation='LTEDG2-120', model_identity='1-2-35',
                                         primary_type='RadioNode'),
                           RadioLoadNode(id='LTEDG202', simulation='LTE-DG2M-120', model_identity='1-2-36',
                                         primary_type='RadioNode')]
        self.exception = Exception("Some Exception")
        self.node_cred = NodeCredentials(self.nodes_list, self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.execute_flow')
    def test_run__in_nodesec_01_is_successful(self, _):
        self.nodesec_01.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.remove')
    def test_task_set_adds_exceptions_on_remove_failure(self, mock_remove, mock_add_error):
        mock_remove.side_effect = self.exception
        self.flow.task_set(self.node_cred, self.flow)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.create')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.remove')
    def test_task_set_adds_exceptions_on_create_failure(self, mock_remove, mock_create, mock_add_error):
        mock_remove.side_effect = None
        mock_create.side_effect = self.exception
        self.flow.task_set(self.node_cred, self.flow)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.restore')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.create')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.remove')
    def test_task_set_adds_exceptions_on_restore_failure(self, mock_remove, mock_create, mock_restore, mock_add_error):
        mock_remove.side_effect = None
        mock_create.side_effect = None
        mock_restore.side_effect = self.exception
        self.flow.task_set(self.node_cred, self.flow)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.create_batches_credential_objects')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.get_nodes_list_by_attribute', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_basic_dictionary_from_list_of_objects')
    def test_execute_01_02_flow(self, mock_nodes, mock_create_and_execute_threads, mock_create_profile_users,
                                mock_state, mock_generate_node_batches, *_):
        mock_nodes.return_value = {"ERBS": [Mock(), Mock()], "RadioNode": [Mock(), Mock()]}
        mock_state.return_value = "RUNNING"
        mock_generate_node_batches.return_value = [mock_nodes.return_value["ERBS"],
                                                   mock_nodes.return_value["RadioNode"]]
        mock_create_profile_users.return_value = [self.user, self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)
        self.assertTrue(mock_generate_node_batches.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.get_nodes_list_by_attribute")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_basic_dictionary_from_list_of_objects")
    def test_execute_create_batches_credential_objects(self, mock_gen_dict, mock_generate_node_batches, *_):
        mock_gen_dict.return_value = {"ERBS": [Mock()], "RadioNode": [Mock()]}
        mock_generate_node_batches.return_value = [["ERBS"],
                                                   ["RadioNode"]]
        result = self.flow.create_batches_credential_objects([self.user, self.user])
        self.assertTrue(len(result) == 4)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches', side_effect=RuntimeError)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_basic_dictionary_from_list_of_objects")
    def test_create_batches_credential_objects__raises_runtime_error(self, mock_gen_dict, mock_add_error_as_exception,
                                                                     *_):
        mock_gen_dict.return_value = {"ERBS": [Mock()], "RadioNode": [Mock()]}
        message = "No available nodes found, please ensure ERBS nodes are created on the deployment."
        self.flow.create_batches_credential_objects([self.user, self.user])
        self.assertTrue(call(EnvironError(message) in mock_add_error_as_exception.mock_calls))


class NodeSec02FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_02 = nodesec_02.NODESEC_02()
        self.flow = NodeSec02Flow()
        self.flow.NUM_BATCHES = 2
        self.nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34', primary_type='ERBS'),
                           ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34',
                                        primary_type='ERBS')]
        self.exception = Exception("Some Exception")
        self.node_cred = NodeCredentials(self.nodes_list, self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec02Flow.execute_flow')
    def test_run__in_nodesec_02_is_successful(self, _):
        self.nodesec_02.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.update')
    def test_task_set_adds_exceptions_on_update_failure(self, mock_update, mock_add_error):
        mock_update.side_effect = self.exception
        self.flow.task_set(self.node_cred, self.flow)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.restore')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.update')
    def test_task_set_adds_exceptions_on_restore_failure(self, mock_update, mock_restore, mock_add_error):
        mock_update.side_effect = None
        mock_restore.side_effect = self.exception
        self.flow.task_set(self.node_cred, self.flow)
        self.assertTrue(mock_add_error.call_count is 1)


class NodeSec03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_03 = nodesec_03.NODESEC_03()
        self.flow = NodeSec03Flow()
        self.nodes_list = [Mock(id='LTE01', simulation='LTE-120', model_identity='1-2-34', poid=1224,
                                node_id='LTE01', primary_type="ERBS"),
                           Mock(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34', poid=1224,
                                node_id='LTE02', primary_type="ERBS")]
        self.exception = Exception("Some Exception")
        self.flow.TEARDOWN = False
        self.start_time = int(time.time())

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.execute_flow')
    def test_run__in_nodesec_03_is_successful(self, _):
        self.nodesec_03.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.check_services_are_online')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.add_error_as_exception')
    def test_services_are_online_adds_exception(self, mock_add_error, mock_check_services_are_online):
        mock_check_services_are_online.side_effect = self.exception
        self.flow.check_services_are_online()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    def test_calculate_and_perform_sleep(self, mock_debug, *_):
        self.flow.calculate_and_perform_sleep(self.start_time, self.nodes_list)
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.get_nodes_not_at_required_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_synchronised_nodes')
    def test_get_nodes_at_correct_security_level__returns_only_correct_nodes(self, mock_get_synchronised_nodes,
                                                                             mock_get_nodes_not_at_required_level):
        mock_get_synchronised_nodes.return_value = self.nodes_list
        mock_get_nodes_not_at_required_level.return_value = ["LTE01"]
        self.assertEqual(self.flow.get_nodes_at_correct_security_level(self.nodes_list, self.user), self.nodes_list[:1])
        self.assertTrue(mock_get_nodes_not_at_required_level.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.get_nodes_not_at_required_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_synchronised_nodes')
    def test_get_nodes_at_correct_security_level__if_synced_nodes_not_found(self, mock_get_synchronised_nodes,
                                                                            mock_get_nodes_not_at_required_level):
        mock_get_synchronised_nodes.return_value = []
        self.assertEqual(self.flow.get_nodes_at_correct_security_level(self.nodes_list, self.user), [])
        self.assertFalse(mock_get_nodes_not_at_required_level.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0.1)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecurityLevel.set_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.add_error_as_exception')
    def test_create_and_execute_security_objects_add_errors_on_set_level(self, mock_add_error, mock_set_level, *_):
        mock_set_level.side_effect = [self.exception, None]
        self.flow.create_and_execute_security_objects([self.nodes_list, self.nodes_list], self.user, self.start_time,
                                                      self.nodes_list, 2)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecurityLevel.set_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.calculate_and_perform_sleep')
    def test_create_and_execute_security_objects_adds_to_teardown(self, mock_calculate_and_sleep, *_):
        self.flow.TEARDOWN = True
        self.flow.create_and_execute_security_objects([self.nodes_list, self.nodes_list], self.user, self.start_time,
                                                      self.nodes_list, 2)
        self.assertTrue(any([isinstance(_, NodeSecurityLevel) for _ in self.flow.teardown_list]))
        self.assertTrue(mock_calculate_and_sleep.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.check_services_are_online')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.'
           'create_and_execute_security_objects')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.'
           'get_nodes_at_correct_security_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__is_successful(self, mock_annotate, mock_get_at_security_level,
                                         mock_create_and_execute_security_objects, mock_get_nodes_list_by_attribute,
                                         *_):
        mock_get_nodes_list_by_attribute.return_value = self.nodes_list
        mock_annotate.return_value = self.nodes_list
        mock_get_at_security_level.side_effect = [self.nodes_list, None]
        self.flow.execute_flow()
        self.assertEqual(mock_annotate.call_count, 1)
        self.assertEqual(mock_create_and_execute_security_objects.call_count, 1)
        self.assertEqual(mock_get_at_security_level.call_count, 2)
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.check_services_are_online')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.'
           'create_and_execute_security_objects')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.'
           'get_nodes_at_correct_security_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__raises_environ_error(self, mock_annotate, mock_get_at_security_level,
                                                mock_generate_node_batches, mock_get_nodes_list_by_attribute, *_):
        mock_get_nodes_list_by_attribute.return_value = self.nodes_list
        mock_annotate.return_value = self.nodes_list
        mock_get_at_security_level.side_effect = [self.nodes_list, None]
        mock_generate_node_batches.side_effect = self.exception
        self.assertRaises(EnvironError, self.flow.execute_flow)
        self.assertEqual(mock_annotate.call_count, 1)
        self.assertEqual(mock_get_at_security_level.call_count, 1)
        mock_get_nodes_list_by_attribute.assert_called_with(node_attributes=["node_id", "poid", "primary_type"])


class NodeSec04FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_04 = nodesec_04.NODESEC_04()
        self.flow = NodeSec04Flow()
        self.nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34'),
                           ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34')]
        self.exception = Exception("Some Exception")
        self.start_time = int(time.time())

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec04Flow.execute_flow')
    def test_run__in_nodesec_04_is_successful(self, _):
        self.nodesec_04.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.nodes_list',
           new_callable=PropertyMock)
    @patch(
        'enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.create_and_execute_security_objects')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.check_services_are_online')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.wait_for_profile')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch(
        'enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_nodes_at_correct_security_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__successful(self, mock_annotate, mock_get_nodes, mock_get_at_security_level,
                                      mock_create_and_execute_security_objects, *_):
        mock_get_nodes.return_value = self.nodes_list
        mock_annotate.return_value = self.nodes_list
        mock_get_at_security_level.side_effect = [self.nodes_list, None]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_security_objects.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.nodes_list',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.check_services_are_online')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.wait_for_profile')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch(
        'enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_nodes_at_correct_security_level')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec03Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.annotate_fdn_poid_return_node_objects')
    def test_execute_flow__raises_environ_error(self, mock_annotate, mock_get_nodes, mock_get_at_security_level,
                                                mock_generate_node_batches, *_):
        mock_get_nodes.return_value = self.nodes_list
        mock_annotate.return_value = self.nodes_list
        mock_get_at_security_level.side_effect = [self.nodes_list, None]
        mock_generate_node_batches.side_effect = self.exception
        self.assertRaises(EnvironError, self.flow.execute_flow)


class NodeSec08FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_08 = nodesec_08.NODESEC_08()
        self.flow = NodeSec08Flow()
        self.flow.NUM_BATCHES = 2
        self.flow.NUM_USERS = 2
        self.nodes_list = [Mock(primary_type="EPG"), Mock(primary_type="RadioNode")]
        self.exception = Exception("Some Exception")
        self.snmp = NodeSNMP(self.nodes_list, self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.execute_flow')
    def test_run__in_nodesec_08_is_successful(self, _):
        self.nodesec_08.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSNMP.set_version')
    def test_task_set_adds_exceptions_set_version_failure(self, mock_set_version, mock_add_error):
        mock_set_version.side_effect = self.exception
        self.flow.task_set(self.snmp, self.flow)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.create_snmp_instances')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.create_and_execute_threads')
    def test_execute_flow__is_successful(self, mock_create_and_execute_threads, mock_get_nodes_by_attribute,
                                         mock_create_profile_users, mock_generate_node_batches,
                                         mock_create_snmp_instances, _):
        mock_get_nodes_by_attribute.return_value = self.nodes_list
        mock_create_profile_users.return_value = [self.user, self.user]
        mock_generate_node_batches.return_value = [[self.nodes_list[0]], [self.nodes_list[1]]]
        self.flow.execute_flow()
        mock_get_nodes_by_attribute.assert_called_with(node_attributes=['node_id', 'primary_type',
                                                                        'snmp_authentication_method',
                                                                        'snmp_auth_password', 'snmp_encryption_method',
                                                                        'snmp_priv_password', 'snmp_security_level',
                                                                        'snmp_security_name'])
        mock_generate_node_batches.assert_called_with(mock_get_nodes_by_attribute.return_value,
                                                      batch_size=self.flow.NUM_BATCHES)
        self.assertTrue(mock_create_snmp_instances.called)
        self.assertTrue(mock_create_profile_users.called)
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.create_snmp_instances')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.generate_node_batches')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec08Flow.create_and_execute_threads')
    def test_execute_flow__raises_environ_error(self, mock_create_and_execute_threads, mock_get_nodes_by_attribute,
                                                mock_create_profile_users, mock_generate_node_batches,
                                                mock_create_snmp_instances, _):
        mock_get_nodes_by_attribute.return_value = []
        mock_generate_node_batches.side_effect = self.exception
        self.assertRaises(EnvironError, self.flow.execute_flow)
        mock_get_nodes_by_attribute.assert_called_with(node_attributes=['node_id', 'primary_type',
                                                                        'snmp_authentication_method',
                                                                        'snmp_auth_password', 'snmp_encryption_method',
                                                                        'snmp_priv_password', 'snmp_security_level',
                                                                        'snmp_security_name'])
        mock_generate_node_batches.assert_called_with([], batch_size=self.flow.NUM_BATCHES)
        self.assertFalse(mock_create_snmp_instances.called)
        self.assertTrue(mock_create_profile_users.called)
        self.assertFalse(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSNMP')
    def test_create_snmp_instances__returns_node_snmp_list(self, mock_nodesnmp):
        mock_batch = Mock()
        mock_user = Mock()
        mock_node_user_tuple = [(mock_batch, mock_user)]
        node_snmp_list = self.flow.create_snmp_instances(mock_node_user_tuple)
        self.assertTrue(len(node_snmp_list) == 1)
        mock_nodesnmp.assert_called_with(nodes=mock_batch, user=mock_user)


class NodeSec11FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_11 = nodesec_11.NODESEC_11()
        self.flow = NodeSec11Flow()
        self.flow.CERTS = ["OAM"]
        self.flow.NUM_USERS = 1
        self.flow.MAX_NODES = 2
        self.flow.USER_ROLES = 'Role'
        self.nodes_list = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                                primary_type="RadioNode", profiles=["NODESEC_11"]),
                           Mock(node_id='LTE02', simulation='LTE-120', model_identity='1-2-34',
                                primary_type="RadioNode", profiles=["NODESEC_11"]),
                           Mock(node_id='LTE03', simulation='LTE-120', model_identity='1-2-34',
                                primary_type="RadioNode", profiles=["NODESEC_11"])]
        self.flow.SCHEDULED_DAYS = "FRIDAY"
        self.flow.SCHEDULED_TIMES_STRINGS = ["18:10:00"]
        self.exception = Exception("Some Exception")
        self.config = SecurityConfig()
        self.cert = NodeCertificate(nodes=self.nodes_list, security_config=self.config, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.execute_flow')
    def test_run__in_nodesec_11_is_successful(self, _):
        self.nodesec_11.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.verify_allocated_nodes_sync_status')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCertificate.issue')
    def test_certificate_issue_tasks__adds_exceptions_issue_failure(self, mock_reissue, mock_add_error, *_):
        mock_reissue.side_effect = self.exception
        self.flow.certificate_issue_tasks(self.cert)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.verify_allocated_nodes_sync_status')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.verify_allocated_nodes_sync_status')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCertificate.issue')
    def test_certificate_issue_tasks__adds_to_teardown(self, mock_reissue, *_):
        mock_reissue.side_effect = None
        self.flow.certificate_issue_tasks(self.cert)
        self.assertTrue(any(isinstance(_, picklable_boundmethod) for _ in self.flow.teardown_list))

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.verify_allocated_nodes_sync_status')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCertificate.reissue')
    def test_certificate_reissue_tasks__adds_exceptions_issue_failure(self, mock_issue, mock_add_error, *_):
        mock_issue.side_effect = self.exception
        self.flow.certificate_reissue_tasks(self.cert)
        self.assertTrue(mock_add_error.call_count is 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    def test_verify_allocated_nodes_sync_status__successful_with_no_unsynced_nodes(self, mock_get_synced_nodes,
                                                                                   mock_log_debug, mock_write_to_file):
        synced_nodes_list = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                                  primary_type="RadioNode", profiles=["NODESEC_11"]),
                             Mock(node_id='LTE02', simulation='LTE-120', model_identity='1-2-34',
                                  primary_type="RadioNode", profiles=["NODESEC_11"]),
                             Mock(node_id='LTE03', simulation='LTE-120', model_identity='1-2-34',
                                  primary_type="RadioNode", profiles=["NODESEC_11"])]
        mock_get_synced_nodes.return_value = synced_nodes_list
        output = self.flow.verify_allocated_nodes_sync_status(self.nodes_list, self.user)
        self.assertEqual(1, mock_get_synced_nodes.call_count)
        self.assertEqual(1, mock_log_debug.call_count)
        self.assertEqual(1, mock_write_to_file.call_count)
        self.assertEqual(output, synced_nodes_list)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    def test_verify_allocated_nodes_sync_status__successful_with_unsynced_nodes(self, mock_get_synced_nodes,
                                                                                mock_log_debug, mock_write_to_file):
        synced_nodes_list = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                                  primary_type="RadioNode", profiles=["NODESEC_11"]),
                             Mock(node_id='LTE02', simulation='LTE-120', model_identity='1-2-34',
                                  primary_type="RadioNode", profiles=["NODESEC_11"])]
        mock_get_synced_nodes.return_value = synced_nodes_list
        output = self.flow.verify_allocated_nodes_sync_status(self.nodes_list, self.user)
        self.assertEqual(1, mock_get_synced_nodes.call_count)
        self.assertEqual(2, mock_log_debug.call_count)
        self.assertEqual(1, mock_write_to_file.call_count)
        self.assertEqual(output, synced_nodes_list)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    def test_verify_allocated_nodes_sync_status__raise_exception(self, mock_get_synced_nodes, mock_log_debug,
                                                                 mock_write_to_file, mock_add_error):
        mock_get_synced_nodes.side_effect = Exception
        self.flow.verify_allocated_nodes_sync_status(self.nodes_list, self.user)
        self.assertEqual(1, mock_get_synced_nodes.call_count)
        self.assertEqual(0, mock_log_debug.call_count)
        self.assertEqual(0, mock_write_to_file.call_count)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.sleep_until_day")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.keep_running",
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.wait_for_profile')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.certificate_issue_tasks')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.certificate_reissue_tasks')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.perform_prerequisites')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSecFlow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_nodes_list_by_attribute')
    def test_execute_flow_11__success(self, mock_nodes_list, mock_create_users, mock_perform_prerequisites,
                                      mock_reissue_tasks, mock_issue_tasks, *_):
        mock_nodes_list.return_value = self.nodes_list
        mock_create_users.return_value = [self.user]
        mock_perform_prerequisites.return_value = MagicMock()
        self.flow.execute_flow()
        self.assertEqual(1, mock_nodes_list.call_count)
        self.assertEqual(1, mock_perform_prerequisites.call_count)
        self.assertEqual(1, mock_create_users.call_count)
        self.assertEqual(1, mock_issue_tasks.call_count)
        self.assertEqual(1, mock_reissue_tasks.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.state', new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.sleep_until_day")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_nodes_list_by_attribute',
           return_value=[])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.keep_running",
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.wait_for_profile')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.certificate_issue_tasks')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.certificate_reissue_tasks')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.perform_prerequisites')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.create_profile_users')
    def test_execute_flow_11__raises_env_error(self, mock_create_users, mock_perform_prerequisites, mock_error,
                                               mock_reissue_tasks, mock_issue_tasks, *_):
        mock_create_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(call(EnvironError('Profile is not allocated to any node') in mock_error.mock_calls))
        self.assertEqual(0, mock_perform_prerequisites.call_count)
        self.assertEqual(1, mock_create_users.call_count)
        self.assertEqual(0, mock_issue_tasks.call_count)
        self.assertEqual(0, mock_reissue_tasks.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    def test_perform_prerequisites__is_success(self, mock_get_synchronised_nodes, mock_debug_log,
                                               mock_update_profile_persistence):
        mock_get_synchronised_nodes.return_value = self.nodes_list
        self.flow.MAX_NODES = 3
        expected_node_list = self.nodes_list
        output = self.flow.perform_prerequisites(self.nodes_list, self.user)
        self.assertEqual(expected_node_list, output)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(0, mock_update_profile_persistence.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    def test_perform_prerequisites__raises_enverror(self, mock_get_synchronised_nodes, mock_debug_log,
                                                    mock_update_profile_persistence):
        mock_get_synchronised_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.perform_prerequisites, self.nodes_list, self.user)
        self.assertEqual(0, mock_debug_log.call_count)
        self.assertEqual(0, mock_update_profile_persistence.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec11Flow.get_synchronised_nodes')
    def test_perform_prerequisites__deallocate_unused_nodes(self, mock_get_synchronised_nodes, mock_debug_log,
                                                            mock_update_profile_persistence):
        synced_nodes = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                             primary_type="RadioNode", profiles=["NODESEC_11"]),
                        Mock(node_id='LTE03', simulation='LTE-120', model_identity='1-2-34',
                             primary_type="RadioNode", profiles=["NODESEC_11"])]
        mock_get_synchronised_nodes.return_value = synced_nodes
        self.flow.MAX_NODES = 1
        expected_node_list = [synced_nodes[0]]
        output = self.flow.perform_prerequisites(self.nodes_list, self.user)
        self.assertEqual(expected_node_list, output)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_update_profile_persistence.call_count)


class NodeSec13FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.nodesec_13 = nodesec_13.NODESEC_13()
        self.flow = NodeSec13Flow()
        self.flow.CERTS = ["OAM"]
        self.flow.MAX_NODES = 3
        self.nodes_list = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                                primary_type="RadioNode"),
                           Mock(node_id='LTE02', simulation='LTE-120', model_identity='1-2-34',
                                primary_type="RadioNode"),
                           Mock(node_id='LTE03', simulation='LTE-120', model_identity='1-2-34',
                                primary_type="RadioNode")]
        self.flow.SCHEDULED_DAYS = "FRIDAY"
        self.flow.SCHEDULED_TIMES_STRINGS = ["22:35:00"]
        self.exception = Exception("Some Exception")
        self.config = SecurityConfig()
        self.trust = NodeTrust(nodes=self.nodes_list, security_config=self.config, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.execute_flow')
    def test_run__in_nodesec_13_is_successful(self, _):
        self.nodesec_13.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.nodes_trust_remove')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.nodes_trust_distribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.trust_prerequisites')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_nodes_list_by_attribute')
    def test_execute_flow__is_success(self, mock_nodes_list, mock_create_profile_users, mock_trust_prerequisites,
                                      mock_nodes_trust_distribute, mock_nodes_trust_remove, *_):
        with patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.'
                   'check_sync_and_unsync_nodes_and_save_to_files') as check_sync_unsync_nodes:

            mock_nodes_list.return_value = self.nodes_list
            mock_create_profile_users.return_value = [self.user]
            mock_trust_prerequisites.return_value = MagicMock()
            self.flow.execute_flow()
            self.assertEqual(1, mock_nodes_list.call_count)
            self.assertEqual(1, mock_trust_prerequisites.call_count)
            self.assertEqual(1, mock_create_profile_users.call_count)
            self.assertEqual(3, mock_nodes_trust_distribute.call_count)
            self.assertEqual(2, mock_nodes_trust_remove.call_count)
            self.assertEqual(3, len(self.flow.teardown_list))
            self.assertEqual(2, check_sync_unsync_nodes.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_nodes_list_by_attribute',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.nodes_trust_remove')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.nodes_trust_distribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.trust_prerequisites')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    def test_execute_flow__raises_env_error_if_nodes_not_exist(self, mock_add_error, mock_create_profile_users,
                                                               mock_trust_prerequisites, mock_nodes_trust_distribute,
                                                               mock_nodes_trust_remove, *_):
        with patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.'
                   'check_sync_and_unsync_nodes_and_save_to_files') as check_sync_unsync_nodes:
            mock_create_profile_users.return_value = [self.user]
            mock_trust_prerequisites.return_value = MagicMock()
            self.flow.execute_flow()
            self.assertTrue(call(EnvironError('Profile is not allocated to any node') in mock_add_error.mock_calls))
            self.assertEqual(0, mock_trust_prerequisites.call_count)
            self.assertEqual(1, mock_create_profile_users.call_count)
            self.assertEqual(0, mock_nodes_trust_distribute.call_count)
            self.assertEqual(0, mock_nodes_trust_remove.call_count)
            self.assertEqual(0, len(self.flow.teardown_list))
            self.assertEqual(0, check_sync_unsync_nodes.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.delete_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.trust_prerequisites',
           return_value=MagicMock())
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.nodes_trust_remove')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.nodes_trust_distribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_nodes_list_by_attribute')
    def test_execute_flow__if_synced_nodes_not_found(self, mock_nodes_list, mock_create_profile_users,
                                                     mock_add_error, mock_nodes_trust_distribute,
                                                     mock_nodes_trust_remove, *_):
        with patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.'
                   'check_sync_and_unsync_nodes_and_save_to_files') as check_sync_unsync_nodes:

            mock_nodes_list.return_value = self.nodes_list
            mock_create_profile_users.return_value = [self.user]
            check_sync_unsync_nodes.side_effect = EnvironError("Synced nodes are not found.")
            self.flow.execute_flow()
            self.assertEqual(1, mock_nodes_list.call_count)
            self.assertEqual(2, mock_add_error.call_count)
            self.assertEqual(1, mock_create_profile_users.call_count)
            self.assertEqual(1, mock_nodes_trust_distribute.call_count)
            self.assertEqual(0, mock_nodes_trust_remove.call_count)
            self.assertEqual(3, len(self.flow.teardown_list))
            self.assertEqual(2, check_sync_unsync_nodes.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeTrust.distribute')
    def test_nodes_trust_distribute__is_success(self, mock_distribute, mock_add_error):
        self.flow.nodes_trust_distribute(self.trust)
        mock_distribute.assert_called("nodes.txt", "/tmp/nodes.txt", include_ca=True)
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeTrust.distribute')
    def test_nodes_trust_distribute__add_error_as_exception(self, mock_distribute, mock_add_error):
        mock_distribute.side_effect = Exception("error")
        self.flow.nodes_trust_distribute(self.trust)
        mock_distribute.assert_called("nodes.txt", "/tmp/nodes.txt", include_ca=True)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeTrust.remove')
    def test_nodes_trust_remove__is_success(self, mock_remove, mock_add_error):
        self.flow.nodes_trust_remove(self.trust)
        mock_remove.assert_called("nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeTrust.remove')
    def test_nodes_trust_remove__add_error_as_exception(self, mock_remove, mock_add_error):
        mock_remove.side_effect = Exception("error")
        self.flow.nodes_trust_remove(self.trust)
        mock_remove.assert_called("nodes.txt", "/tmp/nodes.txt")
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_synchronised_nodes')
    def test_trust_prerequisites__is_success(self, mock_get_synchronised_nodes, mock_debug_log,
                                             mock_write_data_to_file, mock_update_profile_persistence):
        mock_get_synchronised_nodes.return_value = self.nodes_list
        self.flow.trust_prerequisites(self.nodes_list, self.user)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(1, mock_write_data_to_file.call_count)
        self.assertEqual(0, mock_update_profile_persistence.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_synchronised_nodes')
    def test_trust_prerequisites__raises_env_error(self, mock_get_synchronised_nodes, mock_debug_log,
                                                   mock_write_data_to_file, mock_update_profile_persistence):
        mock_get_synchronised_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.trust_prerequisites, self.nodes_list, self.user)
        self.assertEqual(0, mock_debug_log.call_count)
        self.assertEqual(0, mock_write_data_to_file.call_count)
        self.assertEqual(0, mock_update_profile_persistence.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.'
           'update_profile_persistence_nodes_list')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_synchronised_nodes')
    def test_trust_prerequisites__if_unused_nodes_exist(self, mock_get_synchronised_nodes, mock_debug_log,
                                                        mock_write_data_to_file, mock_update_profile_persistence):
        synced_nodes = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                             primary_type="RadioNode"),
                        Mock(node_id='LTE02', simulation='LTE-120', model_identity='1-2-34',
                             primary_type="RadioNode")]
        mock_get_synchronised_nodes.return_value = synced_nodes
        self.flow.MAX_NODES = 1
        self.flow.trust_prerequisites(self.nodes_list, self.user)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_write_data_to_file.call_count)
        self.assertEqual(1, mock_update_profile_persistence.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_synchronised_nodes')
    def test_check_sync_and_unsync_nodes_and_save_to_files__is_successful(self, mock_get_synchronised_nodes,
                                                                          mock_debug_log,
                                                                          mock_write_data_to_file):
        synced_nodes = [Mock(node_id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                             primary_type="RadioNode"),
                        Mock(node_id='LTE02', simulation='LTE-120', model_identity='1-2-34',
                             primary_type="RadioNode")]
        mock_get_synchronised_nodes.return_value = synced_nodes
        self.flow.check_sync_and_unsync_nodes_and_save_to_files(self.trust, self.user)
        self.assertEqual(1, mock_get_synchronised_nodes.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(2, mock_write_data_to_file.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_synchronised_nodes')
    def test_check_sync_and_unsync_nodes_and_save_to_files__if_unsynced_nodes_not_found(self,
                                                                                        mock_get_synchronised_nodes,
                                                                                        mock_debug_log,
                                                                                        mock_write_data_to_file):
        mock_get_synchronised_nodes.return_value = self.nodes_list
        self.flow.check_sync_and_unsync_nodes_and_save_to_files(self.trust, self.user)
        self.assertEqual(1, mock_get_synchronised_nodes.call_count)
        self.assertEqual(1, mock_debug_log.call_count)
        self.assertEqual(2, mock_write_data_to_file.call_count)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec13Flow.get_synchronised_nodes')
    def test_check_sync_and_unsync_nodes_and_save_to_files__if_synced_nodes_not_found(self,
                                                                                      mock_get_synchronised_nodes,
                                                                                      mock_debug_log,
                                                                                      mock_write_data_to_file):
        mock_get_synchronised_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.check_sync_and_unsync_nodes_and_save_to_files, self.trust, self.user)
        self.assertEqual(1, mock_get_synchronised_nodes.call_count)
        self.assertEqual(2, mock_debug_log.call_count)
        self.assertEqual(1, mock_write_data_to_file.call_count)


class NodeSec15FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.user.username = 'Test_20171121111236_u1'
        unit_test_utils.setup()
        self.nodesec_15 = nodesec_15.NODESEC_15()
        self.nodesec_18 = nodesec_18.NODESEC_18()
        self.flow = NodeSec15Flow()
        self.flow.NUM_USERS = 2
        self.flow.SCHEDULED_TIMES_STRINGS = ['08:00:00']
        self.flow.RUN_UNTIL = '18:00:00'
        self.flow.THREAD_QUEUE_TIMEOUT = 1
        self.flow.NODE_REQUEST_CREDENTIALS_TIME = 5
        self.nodes_list = [ERBSLoadNode(id='LTE01', simulation='LTE-120', model_identity='1-2-34',
                                        primary_type='ERBS'),
                           ERBSLoadNode(id='LTE02', simulation='LTE-UPGIND-120', model_identity='1-2-34',
                                        primary_type='ERBS')]
        self.exception = Exception("Some Exception")
        self.node_cred = NodeCredentials(self.nodes_list, self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.execute_flow')
    def test_run__in_nodesec_15_is_successful(self, _):
        self.nodesec_15.run()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.get_credentials_with_delay')
    def test_task_set__successful_on_get_credentials_failure_before_end_time(self, mock_get_credentials_with_delay,
                                                                             mock_add_error, mock_datetime, _):
        mock_datetime.now.return_value = datetime(2018, 1, 1)
        self.flow.end_time = datetime(2019, 1, 1)
        self.flow.task_set(self.node_cred, self.flow)
        self.assertTrue(mock_get_credentials_with_delay.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials.get_credentials_with_delay')
    def test_task_set__successful_on_get_credentials_failure_after_end_time(self, mock_get_credentials_with_delay,
                                                                            mock_datetime, *_):
        mock_datetime.now.return_value = datetime(2020, 1, 1)
        self.flow.end_time = datetime(2019, 1, 1)
        self.flow.task_set(self.node_cred, self.flow)
        self.assertFalse(mock_get_credentials_with_delay.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeCredentials')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.split_list_into_sublists')
    def test_get_credentials_instances__is_successful(self, mock_split_list_into_sublists, mock_node_credentials, _):
        self.flow.get_credentials_instances([Mock(), Mock()], [Mock(), Mock()])
        self.assertEqual(mock_split_list_into_sublists.call_count, 1)
        self.assertEqual(mock_node_credentials.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_credentials_instances')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.'
           'last_iteration_if_minimum_time_exists')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_end_time')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.execute_threads_for_profile')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_nodes_list_by_attribute')
    def test_execute_01_02_flow__success(self, mock_nodes_list, mock_create_users, mock_datetime,
                                         mock_execute_threads_profile, mock_end_time, *_):
        mock_nodes_list.return_value = self.nodes_list
        mock_create_users.return_value = [self.user, self.user]
        now = mock_datetime.now.return_value = datetime.now()
        mock_end_time.return_value = now.replace(hour=18, minute=0, second=0)
        mock_execute_threads_profile.return_value = now.replace(hour=18, minute=7, second=0)
        self.flow.next_iteration_time = datetime(2018, 5, 1)
        self.flow.execute_flow()
        self.assertEqual(1, mock_execute_threads_profile.call_count)
        mock_create_users.assert_called_with(2, roles=["ADMINISTRATOR"])
        self.assertTrue(mock_end_time.called)
        self.assertTrue(mock_nodes_list.called)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.execute_threads_for_profile',
           return_value=datetime(2019, 5, 1))
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.'
           'last_iteration_if_minimum_time_exists')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_end_time',
           return_value=datetime(2019, 1, 1))
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_credentials_instances')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec01Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.keep_running')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.get_nodes_list_by_attribute')
    def test_execute_flow__raise_env_error_if_no_nodes(self, mock_nodes_list, mock_create_users, mock_keep_running,
                                                       mock_add_error_as_exception, *_):
        mock_nodes_list.return_value = []
        mock_create_users.return_value = [self.user, self.user]
        mock_keep_running.side_effect = [True, False]
        self.flow.execute_flow()
        message = "Profile is not allocated to any node"
        self.assertTrue(call(EnvironError(message) in mock_add_error_as_exception.mock_calls))

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    def test_execute_threads_for_profile__successful(self, mock_datetime, mock_threads):
        now = datetime.now()
        now1 = now.replace(hour=12, minute=0, second=0)
        now2 = now.replace(hour=14, minute=0, second=0)
        now3 = now.replace(hour=19, minute=0, second=0)
        next_iteration_time = now.replace(hour=21, minute=0, second=0)
        mock_datetime.now.side_effect = [now1, now2, now3]
        mock_credentials = [Mock(), Mock()]
        self.assertEqual(self.flow.execute_threads_for_profile(mock_credentials), next_iteration_time)
        mock_threads.assert_called_with(mock_credentials, 2, wait=1, args=[self.flow])

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    def test_last_iteration_if_minimum_time_exists__successful(self, mock_date_time, mock_execute_threads):
        now = mock_date_time.return_value = datetime.now()
        self.flow.next_iteration_time = now.replace(hour=18, minute=15, second=0)
        self.flow.end_time = now.replace(hour=18, minute=0, second=0)
        mock_credentials = [Mock(), Mock()]
        self.flow.last_iteration_if_minimum_time_exists(mock_credentials)
        mock_execute_threads.assert_called_with(mock_credentials, 2, wait=1, args=[self.flow])
        self.assertEqual(mock_execute_threads.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec15Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.datetime')
    def test_last_iteration_if_minimum_time_exists__unsuccessful(self, mock_date_time, mock_execute_threads):
        now = mock_date_time.return_value = datetime.now()
        self.flow.next_iteration_time = now.replace(hour=18, minute=45, second=0)
        self.flow.end_time = now.replace(hour=18, minute=0, second=0)
        self.flow.last_iteration_if_minimum_time_exists([Mock(), Mock()])
        self.assertEqual(mock_execute_threads.call_count, 0)


class NodeSec18FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        self.user.username = 'NODESC_18_20171121111236_u1'
        unit_test_utils.setup()
        self.nodesec_18 = nodesec_18.NODESEC_18()
        self.flow = NodeSec18Flow()
        self.flow.NUM_USERS = 1
        self.flow.SCHEDULED_TIMES_STRINGS = ['04:00:00']
        self.flow.SCHEDULED_DAYS = ["MONDAY", "TUESDAY"]
        self.flow.USER_ROLES = ["sshkeymaker"]
        self.flow.CAPABILITIES = {"sshkey": ["create", "delete"], "cm_editor": ["read"]}
        self.job_success_response = ['Job(s) Summary', 'Job Id : 414ab2be-d486-412f-b606-1bce653882ff',
                                     'Command Id : CREATE_SSH_KEY', 'Job User : NODESEC_18_0402-10172988_u0',
                                     'Job Status : COMPLETED', 'Job Start Date : N/A', 'Job End Date : N/A',
                                     'Num Of Workflows : 98', 'Num Of Pending Workflows : 0',
                                     'Num Of Running Workflows : 0',
                                     'Num Of Success Workflows : 90', 'Num Of Error Workflows : 8',
                                     'Min Duration Of Success Workflows : N/A',
                                     'Max Duration Of Success Workflows : N/A',
                                     'Avg Duration Of Success Workflows : N/A']
        self.job_fail_response = ['Job(s) Summary', 'Job Id : 414ab2be-d486-412f-b606-1bce653882ff',
                                  'Command Id : CREATE_SSH_KEY', 'Job User : NODESEC_18_0402-10172988_u0',
                                  'Job Status : COMPLETED', 'Job Start Date : N/A', 'Job End Date : N/A',
                                  'Num Of Workflows : 98', 'Num Of Pending Workflows : 0', 'Num Of Running Workflows : 0',
                                  'Num Of Success Workflows : 38', 'Num Of Error Workflows : 60',
                                  'Min Duration Of Success Workflows : N/A', 'Max Duration Of Success Workflows : N/A',
                                  'Avg Duration Of Success Workflows : N/A']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.execute_flow')
    def test_run__in_nodesec_18_is_successful(self, _):
        self.nodesec_18.run()

    # execute_flow test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.sleep_until_day",
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_profile_required_nodes", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "perform_sshkey_create_and_delete_operations")
    def test_execute_flow__successful(self, mock_perform_sshkey_create_delete, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_perform_sshkey_create_delete.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.sleep_until_day",
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_profile_required_nodes", side_effect=[EnvironError("Nodes are not found")])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "perform_sshkey_create_and_delete_operations")
    def test_execute_flow__if_synced_nodes_not_found(self, mock_perform_sshkey_create_delete, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertFalse(mock_perform_sshkey_create_delete.called)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.sleep_until_day",
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_profile_required_nodes",
           side_effect=[EnvironError("Profile should be allocate with minimum 90% nodes in deployment.")])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.create_custom_user_role",
           return_value=(Mock(), Mock()))
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "perform_sshkey_create_and_delete_operations")
    def test_execute_flow__if_nodes_are_less(self, mock_perform_sshkey_create_delete, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertFalse(mock_perform_sshkey_create_delete.called)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.sleep_until_day",
           return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_profile_required_nodes", return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep", return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.create_profile_users",
           return_value=[Mock()])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.create_custom_user_role",
           side_effect=[EnvironError("error")])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.state",
           new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.keep_running",
           side_effect=[True, False])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "perform_sshkey_create_and_delete_operations")
    def test_execute_flow__add_error_as_exception(self, mock_perform_sshkey_create_delete, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertFalse(mock_perform_sshkey_create_delete.called)
        self.assertTrue(mock_add_error.called)

    # perform_sshkey_create_and_delete_operations test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.create_sshkey_on_nodes")
    def test_perform_sshkey_create_and_delete_operations__is_successful(self, mock_create_sshkey, mock_delete_sshkey):
        self.flow.perform_sshkey_create_and_delete_operations(self.user, [Mock(), Mock()])
        self.assertEqual(mock_delete_sshkey.call_count, 2)
        self.assertEqual(mock_create_sshkey.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.create_sshkey_on_nodes")
    def test_perform_sshkey_create_and_delete_operations__if_first_run(self, mock_create_sshkey, mock_delete_sshkey):
        self.flow.perform_sshkey_create_and_delete_operations(self.user, [Mock(), Mock()], is_first_run=True)
        self.assertEqual(mock_delete_sshkey.call_count, 2)
        self.assertEqual(mock_create_sshkey.call_count, 1)

    # delete_sshkey_on_nodes test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_any_nodes_in_error_state")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_delete_sshkey_on_nodes__is_successful(self, mock_debug_log, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u"Successfully started a job to delete SSH key. "
                                            u"Perform 'secadm job get -j ac030f38-18cd-4d18-bbd6-a72e9a7d735d' "
                                            u"to get progress info."]
        self.flow.delete_sshkey_on_nodes(self.user, [Mock(node_id="1"), Mock(node_id="2")])
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_any_nodes_in_error_state")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_delete_sshkey_on_nodes__if_first_run(self, mock_debug_log, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u"Successfully started a job to delete SSH key. "
                                            u"Perform 'secadm job get -j ac030f38-18cd-4d18-bbd6-a72e9a7d735d' "
                                            u"to get progress info."]
        self.flow.delete_sshkey_on_nodes(self.user, [Mock(node_id="1"), Mock(node_id="2")], is_first_run=True)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_any_nodes_in_error_state")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_delete_sshkey_on_nodes__add_error(self, mock_debug_log, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u"Internal error"]
        self.flow.delete_sshkey_on_nodes(self.user, [Mock(node_id="1"), Mock(node_id="2")])
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_any_nodes_in_error_state")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_delete_sshkey_on_nodes__when_teardown_is_true(self, mock_debug_log, mock_get_current_job_status,
                                                           mock_check_any_nodes_error_status, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u"Successfully started a job to delete SSH key. "
                                            u"Perform 'secadm job get -j ac030f38-18cd-4d18-bbd6-a72e9a7d735d' "
                                            u"to get progress info."]
        self.flow.delete_sshkey_on_nodes(self.user, [Mock(node_id="1"), Mock(node_id="2")], is_teardown=True)
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_get_current_job_status.call_count, 0)
        self.assertEqual(mock_check_any_nodes_error_status.call_count, 0)

    # create_sshkey_on_nodes test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_any_nodes_in_error_state")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_create_sshkey_on_nodes__is_successful(self, mock_debug_log, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u"Successfully started a job for creating SSH key. "
                                            u"Perform 'secadm job get -j ac030f38-18cd-4d18-bbd6-a72e9a7d735d' "
                                            u"to get progress info."]
        self.flow.create_sshkey_on_nodes(self.user, [Mock(node_id="1"), Mock(node_id="2")])
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_any_nodes_in_error_state")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.check_profile_memory_usage")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_create_sshkey_on_nodes__add_error(self, mock_debug_log, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = [u"Internal error"]
        self.flow.create_sshkey_on_nodes(self.user, [Mock(node_id="1"), Mock(node_id="2")])
        self.assertEqual(mock_debug_log.call_count, 2)

    # get_sshkey_create_and_delete_commands_fail_percentage_on_nodes test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_matched_line_based_on_specific_string")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_get_sshkey_create_and_delete_commands_fail_percentage_on_nodes__is_successful(
            self, mock_debug_log, mock_get_matched_line_based_on_specific_string, _):
        response = Mock()
        response.get_output.return_value = self.job_success_response
        mock_get_matched_line_based_on_specific_string.side_effect = 11 * [""] + ["Num Of Error Workflows : 8"] + 4 * [""]
        self.flow.get_sshkey_create_and_delete_commands_fail_percentage_on_nodes(response, "create",
                                                                                 98)
        self.assertEqual(mock_debug_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_matched_line_based_on_specific_string")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_get_sshkey_create_and_delete_commands_fail_percentage_on_nodes__if_error_not_found(
            self, mock_debug_log, mock_get_matched_line_based_on_specific_string, _):
        response = Mock()
        response.get_output.return_value = ['Job(s) Summary', 'Job Id : 414ab2be-d486-412f-b606-1bce653882ff',
                                            'Command Id : CREATE_SSH_KEY', 'Job User : NODESEC_18_0402-10172988_u0',
                                            'Job Status : COMPLETED', 'Job Start Date : N/A', 'Job End Date : N/A',
                                            'Num Of Workflows : 98', 'Num Of Pending Workflows : 0',
                                            'Num Of Running Workflows : 0',
                                            'Num Of Success Workflows : 90',
                                            'Min Duration Of Success Workflows : N/A',
                                            'Max Duration Of Success Workflows : N/A',
                                            'Avg Duration Of Success Workflows : N/A']
        mock_get_matched_line_based_on_specific_string.return_value = []
        self.flow.get_sshkey_create_and_delete_commands_fail_percentage_on_nodes(response, "create",
                                                                                 98)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_matched_line_based_on_specific_string")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_get_sshkey_create_and_delete_commands_fail_percentage_on_nodes__if_failed_precentage_is_high(
            self, mock_debug_log, mock_get_matched_line_based_on_specific_string, mock_add_error):
        response = Mock()
        response.get_output.return_value = self.job_fail_response
        mock_get_matched_line_based_on_specific_string.side_effect = 11 * [""] + ["Num Of Error Workflows : 60"] + 4 * [""]
        self.flow.get_sshkey_create_and_delete_commands_fail_percentage_on_nodes(response, "create",
                                                                                 98)
        self.assertEqual(mock_debug_log.call_count, 3)
        self.assertEqual(mock_add_error.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_matched_line_based_on_specific_string")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_get_sshkey_create_and_delete_commands_fail_percentage_on_nodes__if_fail_precentage_is_high_for_first_run(
            self, mock_debug_log, mock_get_matched_line_based_on_specific_string, mock_add_error):
        response = Mock()
        response.get_output.return_value = self.job_fail_response
        mock_get_matched_line_based_on_specific_string.side_effect = 11 * [""] + [
            "Num Of Error Workflows : 60"] + 4 * [""]
        self.flow.get_sshkey_create_and_delete_commands_fail_percentage_on_nodes(response, "create",
                                                                                 98, is_first_run=True)
        self.assertEqual(mock_debug_log.call_count, 4)
        self.assertEqual(mock_add_error.call_count, 0)

    # get_matched_line_based_on_specific_string test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.findall", return_value=True)
    def test_get_matched_line_based_on_specific_string__returns_true(self, _):
        self.assertTrue(self.flow.get_matched_line_based_on_specific_string("Num Of Error Workflows : 60",
                                                                            "Num Of Error Workflows"))

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.findall", return_value=False)
    def test_get_matched_line_based_on_specific_string__returns_false(self, _):
        self.assertFalse(self.flow.get_matched_line_based_on_specific_string("Num Of Error Workflows : 60",
                                                                             "Num Of success Workflows"))

    # get_current_job_status test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_sshkey_create_and_delete_commands_fail_percentage_on_nodes")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    def test_get_current_job_status__if_job_status_is_completed(self, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Job Status : COMPLETED"]
        user.enm_execute.return_value = response
        self.flow.get_current_job_status(user, 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f',
                                         "create", 98)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_sshkey_create_and_delete_commands_fail_percentage_on_nodes")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    def test_get_current_job_status__if_first_run(self, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Job Status : COMPLETED"]
        user.enm_execute.return_value = response
        self.flow.get_current_job_status(user, 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f',
                                         "create", 98, is_first_run=True)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_sshkey_create_and_delete_commands_fail_percentage_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.time.sleep', return_value=10)
    def test_get_current_job_status__if_job_status_is_not_completed(self, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = ["Job Status : PENDING"]
        user.enm_execute.return_value = response
        self.assertRaises(EnvironError, self.flow.get_current_job_status, user,
                          'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f', "delete", 98)

    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_proxy_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_sshkey_create_and_delete_commands_fail_percentage_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    def test_get_current_job_status__if_job_status_raises_error(self, mock_add_error, *_):
        self.flow.MAX_POLL = 3
        user, response = Mock(), Mock()
        response.get_output.return_value = Exception
        user.enm_execute.return_value = response
        self.flow.get_current_job_status(user, 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f',
                                         "delete", 98)
        self.assertEqual(mock_add_error.call_count, 1)

    # check_any_nodes_in_error_state test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_matched_line_based_on_specific_string", return_value=['ERROR'])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_check_any_nodes_in_error_state__success(self, mock_log_debug, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = ['\t\t\t\t\t\tCORE04EPGOI100K004\tERROR\t2024-04-03 11:55:42\t00:00:00.345'
                                            '\t[Delete ENM SSH Key: DELETED_ON_ENM][Modeled SSH Key failed]'
                                            '\t[ERROR: Missing MO of type [user] and name [netsim]]\tN/A']
        self.flow.check_any_nodes_in_error_state(self.user,
                                                 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f',
                                                 "delete")
        self.assertTrue(mock_log_debug.called)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow."
           "NodeSec18Flow.get_matched_line_based_on_specific_string", return_value=[])
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    def test_check_any_nodes_in_error_state__if_errors_are_not_found(self, mock_log_debug, *_):
        response = self.user.enm_execute.return_value
        response.get_output.return_value = ['\t\t\t\t\t\tCORE04EPGOI100K004\tERROR\t2024-04-03 11:55:42\t00:00:00.345'
                                            '\t[Delete ENM SSH Key: DELETED_ON_ENM][Modeled SSH Key failed]'
                                            '\t[ERROR: Missing MO of type [user] and name [netsim]]\tN/A']
        self.flow.check_any_nodes_in_error_state(self.user,
                                                 'secadm job get -j 13bdb505-ca8f-48f1-abda-2374f60d0d2f',
                                                 "delete")
        self.assertTrue(mock_log_debug.called)

    # get_total_number_of_sgsn_mme_nodes_on_deployment test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.compile")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.split")
    def test_get_total_number_of_sgsn_mme_nodes_on_deployment__is_successful(self, mock_re_split, mock_re_compile, _):
        response = Mock()
        response.get_output.return_value = "NetworkElement 80 instance(s) found"
        self.user.enm_execute.return_value = response
        mock_re_split.return_value = ["", "80"]
        mock_re_compile.return_value.search.return_value = True
        result = self.flow.get_total_number_of_sgsn_mme_nodes_on_deployment(self.user)
        self.assertEqual(result, 80)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.compile")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.split")
    def test_get_total_number_of_sgsn_mme_nodes_on_deployment__if_nodes_not_found(self, mock_re_split, mock_re_compile,
                                                                                  _):
        response = Mock()
        response.get_output.return_value = "0 instance(s) found"
        self.user.enm_execute.return_value = response
        mock_re_split.return_value = ["", "0"]
        mock_re_compile.return_value.search.side_effect = [None, True]
        result = self.flow.get_total_number_of_sgsn_mme_nodes_on_deployment(self.user)
        self.assertEqual(result, 0)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.split")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.compile")
    def test_get_total_number_of_sgsn_mme_nodes_on_deployment__does_not_match_pattern(self, mock_re_compile, *_):
        response = Mock()
        response.get_output.return_value = "Error : 508 response error"
        self.user.enm_execute.return_value = response
        mock_re_compile.return_value.search.side_effect = [None, None]
        result = self.flow.get_total_number_of_sgsn_mme_nodes_on_deployment(self.user)
        self.assertEqual(result, 0)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.split")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.re.compile")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.add_error_as_exception")
    def test_get_total_number_of_nodes_on_deployment_adds_error_as_exception(self, mock_add_error, *_):
        self.user.enm_execute.side_effect = Exception
        self.flow.get_total_number_of_sgsn_mme_nodes_on_deployment(self.user)
        self.assertTrue(mock_add_error.called)

    # get_profile_required_nodes test cases
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_total_number_of_sgsn_mme_nodes_on_deployment", return_value=80)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.all_nodes_in_workload_pool")
    def test_get_profile_required_nodes__is_successful(self, mock_nodes, mock_sync_nodes, *_):
        nodes = [Mock(node_id=i) for i in range(80)]
        mock_nodes.return_value = nodes
        mock_sync_nodes.return_value = nodes[:73]
        self.flow.get_profile_required_nodes(self.user)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_total_number_of_sgsn_mme_nodes_on_deployment", return_value=0)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.all_nodes_in_workload_pool")
    def test_get_profile_required_nodes__if_sgsn_nodes_are_not_found(self, mock_nodes, mock_sync_nodes, *_):
        nodes = [Mock(node_id=i) for i in range(80)]
        mock_nodes.return_value = nodes
        mock_sync_nodes.return_value = nodes[:73]
        self.assertRaises(EnvironError, self.flow.get_profile_required_nodes, self.user)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_total_number_of_sgsn_mme_nodes_on_deployment", return_value=80)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.all_nodes_in_workload_pool")
    def test_get_profile_required_nodes__nodes_allocated_with_less_than_ninty_percentage(self, mock_nodes,
                                                                                         mock_sync_nodes, *_):
        nodes = [Mock(node_id=i) for i in range(80)]
        mock_nodes.return_value = nodes
        mock_sync_nodes.return_value = nodes[:50]
        self.assertRaises(EnvironError, self.flow.get_profile_required_nodes, self.user)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_total_number_of_sgsn_mme_nodes_on_deployment", return_value=80)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.all_nodes_in_workload_pool")
    def test_get_profile_required_nodes__if_synced_nodes_not_found(self, mock_nodes, mock_sync_nodes, *_):
        nodes = [Mock(node_id=i) for i in range(80)]
        mock_nodes.return_value = nodes
        mock_sync_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.get_profile_required_nodes, self.user)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_total_number_of_sgsn_mme_nodes_on_deployment", return_value=80)
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.all_nodes_in_workload_pool")
    def test_get_profile_required_nodes__if_partial_is_item_exists(self, mock_nodes, mock_sync_nodes, *_):
        nodes = [Mock(node_id=i) for i in range(80)]
        mock_nodes.return_value = nodes
        mock_sync_nodes.return_value = nodes[:74]
        self.flow.teardown_list.append(partial(picklable_boundmethod(self.flow.delete_sshkey_on_nodes), self.user,
                                               [], is_teardown=True))
        self.flow.get_profile_required_nodes(self.user)

    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "get_total_number_of_sgsn_mme_nodes_on_deployment", return_value=80)
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.picklable_boundmethod')
    @patch('enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.partial')
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.delete_sshkey_on_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.nodesec_flows.nodesec_flow.NodeSec18Flow.all_nodes_in_workload_pool")
    def test_get_profile_required_nodes__if_num_nodes_value_is_different(self, mock_nodes, mock_sync_nodes, *_):
        nodes = [Mock(node_id=i) for i in range(80)]
        mock_nodes.return_value = nodes
        self.flow.num_nodes = 75
        mock_sync_nodes.return_value = nodes[:80]
        self.flow.get_profile_required_nodes(self.user)
        self.assertEqual(self.flow.num_nodes, 80)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
