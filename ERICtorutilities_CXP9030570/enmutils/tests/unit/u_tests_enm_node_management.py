#!/usr/bin/env python
import unittest2
from mock import patch, Mock, PropertyMock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.enm_node import ERBSNode, BSCNode
from enmutils.lib.enm_node_management import (CmManagement, FmManagement, ShmManagement, EnmApplicationError,
                                              PmManagement)
from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.netex import Collection
from testslib import unit_test_utils
from testslib.unit_test_utils import generate_configurable_ip


class ManagementUnitTests(ParameterizedTestCase):
    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()

        self.erbs_node1 = ERBSNode(
            "netsim_LTE04ERBS00003", "255.255.255.255", "5.1.120", "1094-174-285", security_state='ON', normal_user='test',
            normal_password='test', secure_user='test', secure_password='test', subnetwork='SubNetwork=ERBS-SUBNW-1', netsim="netsimlin704", simulation="LTE01", user=self.user)

        self.erbs_node2 = ERBSNode(
            "netsim_LTE04ERBS00004", "255.255.255.250", "5.1.120", "1094-174-285", security_state='ON', normal_user='test',
            normal_password='test', secure_user='test', secure_password='test', subnetwork='SubNetwork=ERBS-SUBNW-1', netsim="netsimlin704", simulation="LTE02", user=self.user)

        self.nodes = [self.erbs_node1, self.erbs_node2]
        self.bsc1 = BSCNode(node_id="BSC01", node_ip=generate_configurable_ip(), primary_type="BSC", user=self.user, oss_prefix="")
        self.bsc2 = BSCNode(node_id="BSC02", node_ip=generate_configurable_ip(), primary_type="BSC", user=self.user, oss_prefix="")
        self.bsc_node_ids = [self.bsc1.node_id, self.bsc2.node_id]

        self.collections = [Collection(self.user, "test_collection_1", nodes=[self.erbs_node1]) for _ in range(2)]
        self.cm_obj = CmManagement.get_management_obj(self.nodes, user=self.user)
        self.shm_obj = ShmManagement(node_ids=self.bsc_node_ids, user=self.user, ne_type="BSC")
        self.pm_obj = PmManagement.get_management_obj(self.nodes, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_network_elements_property(self):
        user = Mock()
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "LTE01", "LTE02"
        nodes = [node, node1]
        expected = "LTE01;LTE02"
        cm_obj = CmManagement.get_management_obj(nodes=nodes, user=user)
        self.assertEqual(expected, cm_obj.network_elements)
        cm_obj = CmManagement.get_management_obj(user=user)
        expected = "*"
        self.assertEqual(expected, cm_obj.network_elements)
        expected = "LTE;RadioNode"
        cm_obj.regex = expected
        self.assertEqual(expected, cm_obj.network_elements)

    def test_supervise_raises_exception_when_supervisation_fails_on_one_or_more_nodes(self):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.cm_obj.supervise)

    def test_node_supervision_success(self):
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response

        try:
            self.cm_obj.supervise()
        except ScriptEngineResponseValidationError:
            self.fail("Shouldn't have raised an exception")

    def test_supervise_failure_with_unhandled_error(self):
        response = Mock()
        response.get_output.return_value = [u'Unhandled system error 9999']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.cm_obj.supervise)

    def test_unsupervise_raises_exception_when_unsupervise_fails_on_one_or_more_nodes(self):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.cm_obj.unsupervise)

    def test_unsupervise_failure_with_unhandled_error(self):
        response = Mock()
        response.get_output.return_value = [u'Something went wrong again']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.cm_obj.unsupervise)

    def test_supervise_regex_valid(self):
        cm_obj = CmManagement(user=self.user, regex="*LTE*")
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        try:
            cm_obj.supervise()
        except ScriptEngineResponseValidationError:
            self.fail("Shouldn't have raised an exception")

    def test_supervise_regex_invalid(self):
        cm_obj = CmManagement(user=self.user, regex="*not_a_valid_node*")
        response = Mock()
        response.get_output.return_value = [u'0 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, cm_obj.supervise)

    def test_supervise_all_pass(self):
        cm_obj = CmManagement.get_management_obj(user=self.user)
        response = Mock()
        response.get_output.return_value = [u'1789 instance(s) updated']
        self.user.enm_execute.return_value = response
        try:
            cm_obj.supervise()
        except ScriptEngineResponseValidationError:
            self.fail("Shouldn't have raised an exception")

    def test_supervise_all_returns_zero(self):
        cm_obj = CmManagement.get_management_obj(user=self.user)
        response = Mock()
        response.get_output.return_value = [u'0 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, cm_obj.supervise)

    def test_synchronize_pass(self):
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        try:
            self.cm_obj.synchronize()
        except ScriptEngineResponseValidationError:
            self.fail("Shouldn't have raised an exception")

    @patch('enmutils.lib.enm_node_management.ShmManagement._verify_sync_operation')
    def test_synchronize__verify_sync(self, mock_verify):
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.shm_obj.synchronize()
        self.assertEqual(1, mock_verify.call_count)

    def test_synchronize__pass_with_ne_type(self):
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        try:
            self.cm_obj.synchronize(netype='RadioNode')
        except ScriptEngineResponseValidationError:
            self.fail("Shouldn't have raised an exception")

    def test_synchronize_failure_if_object_not_take_ne_type(self):
        fm_obj = FmManagement.get_management_obj(self.nodes, user=self.user)
        self.assertRaises(RuntimeError, fm_obj.synchronize, netype='RadioNode')

    def test_synchronize_pass_with_collection(self):
        cm_obj = CmManagement.get_management_obj(collections=self.collections, user=self.user)
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        try:
            cm_obj.synchronize()
        except ScriptEngineResponseValidationError:
            self.fail("Shouldn't have raised an exception")

    @patch('enmutils.lib.enm_node_management.ShmManagement.get_status')
    def test_get_inventory_sync_nodes_success(self, mock_status):
        mock_status.return_value = {u'CORE42ML02': u'SYNCHRONIZED', u'CORE42ML01': u'UNSYNCHRONIZED'}
        self.shm_obj.get_inventory_sync_nodes()

    @patch('enmutils.lib.enm_node_management.ShmManagement.get_status')
    def test_get_inventory_sync_nodes_empty_status(self, mock_status):
        mock_status.get_status.return_value = {}
        self.shm_obj.get_inventory_sync_nodes()

    @patch('enmutils.lib.enm_node_management.Management')
    def test_get_status_success_match(self, *_):
        response = Mock()
        response.get_output.return_value = [u'',
                                            u' : NetworkElement=CORE42ML02,SHMFunction=1,'
                                            u' 'u'InventoryFunction=1,syncStatus : UNSYNCHRONIZED,,',
                                            u' : NetworkElement=CORE42ML01,SHMFunction=1,'
                                            u'InventoryFunction=1,syncStatus : UNSYNCHRONIZED,,,2 instance(s)']
        self.user.enm_execute.return_value = response
        ShmManagement.get_status(self.user, node_ids=['CORE42ML01', 'CORE42ML02'])

    @patch('enmutils.lib.enm_node_management.Management')
    def test_get_status_success_no_match(self, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'InventoryFunction=1,syncStatus : UNSYNCHRONIZED,,']
        self.user.enm_execute.return_value = response
        ShmManagement.get_status(self.user)

    @patch('enmutils.lib.cache.has_key', return_value=True)
    @patch('enmutils.lib.cache.get', return_value=True)
    def test_get_status_success_no_match_cpp_filter(self, mock_get, *_):
        response = Mock()
        response.get_output.return_value = [u'', u'InventoryFunction=1,syncStatus : UNSYNCHRONIZED,,']
        self.user.enm_execute.return_value = response
        ShmManagement.get_status(self.user)
        self.assertEqual(1, mock_get.call_count)

    @patch('enmutils.lib.enm_node_management.Management')
    def test_node_supervise_success_for_ne_type(self, *_):
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.shm_obj.supervise()

    @patch('enmutils.lib.enm_node_management.Management')
    def test_node_supervise_success_for_other_nodes(self, *_):
        shm_obj = ShmManagement(user=self.user, ne_type="MSC")
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        shm_obj.supervise()

    @patch('enmutils.lib.enm_node_management.Management')
    def test_node_supervise_success_for_node_ids(self, *_):
        node_id = ["BSC01"]
        shm_obj = ShmManagement(user=self.user, node_ids=node_id)
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        self.user.enm_execute.return_value = response
        shm_obj.supervise()

    @patch('enmutils.lib.enm_node_management.Management')
    def test_node_unsupervise_success_for_ne_type(self, *_):
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        self.shm_obj.unsupervise()

    @patch('enmutils.lib.enm_node_management.Management')
    def test_node_unsupervise_success_for_other_nodes(self, *_):
        shm_obj = ShmManagement(user=self.user, ne_type="MSC")
        response = Mock()
        response.get_output.return_value = [u'2 instance(s) updated']
        self.user.enm_execute.return_value = response
        shm_obj.unsupervise()

    @patch('enmutils.lib.enm_node_management.Management')
    def test_node_unsupervise_success_for_node_ids(self, *_):
        node_id = ["BSC01"]
        shm_obj = ShmManagement(user=self.user, node_ids=node_id)
        response = Mock()
        response.get_output.return_value = [u'1 instance(s) updated']
        self.user.enm_execute.return_value = response
        shm_obj.unsupervise()

    @patch('enmutils.lib.log.logger.debug')
    def test_cm_verify_sync_operation__success(self, mock_debug):
        response = Mock()
        response.get_output.return_value = [u'SUCCESS FDN : NetworkElement=LTE04dg2ERBS00009,CmFunction=1',
                                            u'SUCCESS FDN : NetworkElement=LTE04dg2ERBS00007,CmFunction=1',
                                            u'2 instance(s) updated']
        self.cm_obj._verify_sync_operation(response)
        mock_debug.assert_called_with('Successfully executed Cm synchronize for 2 nodes.')

    def test_cm_verify_sync_operation__raises_script_engine_error(self):
        response = None
        self.assertRaises(ScriptEngineResponseValidationError, self.cm_obj._verify_sync_operation, response)

    def test_cm_verify_sync_operation__raises_enm_application_error(self):
        response = Mock()
        response.get_output.return_value = [u'SUCCESS FDN : NetworkElement=LTE04dg2ERBS00009,CmFunction=1',
                                            u'SUCCESS FDN : NetworkElement=LTE04dg2ERBS00007,CmFunction=1',
                                            u'FAILED FDN : NetworkElement=LTE04dg2ERBS00003,CmFunction=1'
                                            u'Error 5008 : The command executed on 2 out of 3 objects']
        self.assertRaises(EnmApplicationError, self.cm_obj._verify_sync_operation, response)

    def test_check_generation_counter__success(self):
        response = Mock()
        response.get_output.return_value = []
        self.user.enm_execute.return_value = response
        self.cm_obj.check_generation_counter("Node", self.user)

    def test_check_generation_counter__raises_script_engine_validation_error(self):
        response = Mock()
        response.get_output.return_value = [self.cm_obj.CHECK_GENERATION_COUNTER]
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.cm_obj.check_generation_counter, "Node", self.user)

    @patch('enmutils.lib.enm_node_management.re.search')
    @patch('enmutils.lib.enm_node_management.re.findall')
    def test_verify_sync_operation__error_match(self, mock_findall, mock_search):
        mock_search_result = Mock()
        mock_search_result.group.return_value = 1
        mock_findall.return_value = []
        mock_search.return_value = mock_search_result
        response, collection, node = Mock(), Mock(), Mock(node_id="Node")
        collection.nodes = [node]
        response.get_output.return_value = []
        self.assertRaises(ScriptEngineResponseValidationError, self.shm_obj._verify_sync_operation,
                          response, collections=[collection])

    @patch('enmutils.lib.enm_node_management.re.search')
    @patch('enmutils.lib.enm_node_management.re.findall')
    @patch('enmutils.lib.enm_node_management.ShmManagement._check_instance_match')
    def test_verify_sync_operation__checks_instance_match(self, mock_check, mock_findall, _):
        mock_findall_result = [Mock()]
        mock_findall.side_effect = [mock_findall_result]
        response = Mock()
        response.get_output.return_value = []
        self.shm_obj._verify_sync_operation(response)
        self.assertEqual(1, mock_check.call_count)

    @patch('enmutils.lib.enm_node_management.re.search')
    def test_verify_sync_operation__raises_script_engine_validation_error(self, mock_search):
        mock_search.return_value = None
        response = Mock()
        response.get_output.return_value = []
        self.assertRaises(ScriptEngineResponseValidationError, self.shm_obj._verify_sync_operation, response)

    @patch('enmutils.lib.enm_node_management.CmManagement.network_elements', new_callable=PropertyMock,
           return_value="*")
    @patch('enmutils.lib.enm_node_management.re.search')
    @patch('enmutils.lib.enm_node_management.log.logger.debug')
    def test_check_instance_match__all_nodes_success(self, mock_debug, mock_search, _):
        mock_search.return_value = True
        instances_match, response = [30], Mock()
        response.get_output.return_value = "Successfully executed Cm synchronize for 30 nodes using *."
        self.cm_obj._check_instance_match(instances_match, response, 30)
        mock_debug.assert_called_with('Successfully executed Cm synchronize for 30 nodes using *.')

    @patch('enmutils.lib.enm_node_management.re.search')
    @patch('enmutils.lib.enm_node_management.log.logger.debug')
    def test_check_instance_match__no_regex_success(self, mock_debug, mock_search):
        mock_search.return_value = True
        instances_match, response = [21], Mock()
        self.cm_obj._check_instance_match(instances_match, response, 21)
        mock_debug.assert_called_with('Successfully executed Cm synchronize for netsim_LTE04ERBS00003,'
                                      'netsim_LTE04ERBS00004 nodes.')

    @patch('enmutils.lib.enm_node_management.CmManagement.network_elements', new_callable=PropertyMock,
           return_value="*")
    @patch('enmutils.lib.enm_node_management.re.search')
    def test_check_instance_match__regex_failure_on_all_nodes(self, mock_search, _):
        mock_search.return_value = False
        instances_match, response = [1], Mock()
        self.assertRaises(ScriptEngineResponseValidationError,
                          self.cm_obj._check_instance_match, instances_match, response, 1)

    @patch('enmutils.lib.enm_node_management.CmManagement.network_elements', new_callable=PropertyMock,
           return_value="*")
    @patch('enmutils.lib.enm_node_management.re.search')
    def test_check_instance_match__regex_failure(self, mock_search, _):
        mock_search.return_value = True
        instances_match, response = [1, 30], Mock()
        self.assertRaises(ScriptEngineResponseValidationError,
                          self.cm_obj._check_instance_match, instances_match, response, 1)

    @patch('enmutils.lib.enm_node_management.re.search')
    def test_check_instance_match__failure(self, mock_search):
        mock_search.return_value = False
        instances_match, response = [10], Mock()
        self.assertRaises(ScriptEngineResponseValidationError,
                          self.cm_obj._check_instance_match, instances_match, response, 10)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
