#!/usr/bin/env python
import unittest2
from enmutils_int.lib.services import nodemanager_helper_methods
from enmutils_int.lib import node_pool_mgr
from mock import patch, Mock, call
from testslib import unit_test_utils
from enmutils.lib.exceptions import EnmApplicationError


class NodeManagerHelperMethodsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.mutexer.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.poid_refresh")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.update_poid_attribute_on_nodes")
    def test_update_poid_attributes_on_pool_nodes__successful_if_nodes_exist(
            self, mock_update_poid_attribute_on_nodes, mock_poid_refresh, *_):
        node_pool_mgr.cached_nodes_list = [Mock()]
        nodemanager_helper_methods.update_poid_attributes_on_pool_nodes()
        mock_update_poid_attribute_on_nodes.assert_called_with(mock_poid_refresh.return_value)
        self.assertTrue(mock_poid_refresh.called)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.poid_refresh")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.update_poid_attribute_on_nodes")
    def test_update_poid_attributes_on_pool_nodes__no_pool_nodes(
            self, mock_update_poid_attribute_on_nodes, mock_poid_refresh, *_):
        node_pool_mgr.cached_nodes_list = []
        nodemanager_helper_methods.update_poid_attributes_on_pool_nodes()
        self.assertFalse(mock_update_poid_attribute_on_nodes.called)
        self.assertFalse(mock_poid_refresh.called)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.poid_refresh", return_value={})
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.update_poid_attribute_on_nodes")
    def test_update_poid_attributes_on_pool_nodes__no_poid_data(
            self, mock_update_poid_attribute_on_nodes, mock_poid_refresh, *_):
        node_pool_mgr.cached_nodes_list = [Mock()]
        nodemanager_helper_methods.update_poid_attributes_on_pool_nodes()
        self.assertFalse(mock_update_poid_attribute_on_nodes.called)
        self.assertTrue(mock_poid_refresh.called)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.log.logger.debug")
    def test_update_poid_attribute_on_nodes__empty_poid_node_dictionary_raises_error(self, *_):
        node_poid_data = {}
        node1 = Mock(node_id="node1", poid="")
        node2 = Mock(node_id="node2", poid="23456")
        node_pool_mgr.cached_nodes_list = [node1, node2]
        with self.assertRaises(EnmApplicationError) as e:
            nodemanager_helper_methods.update_poid_attribute_on_nodes(node_poid_data)
        self.assertEqual(str(e.exception), 'Length of node_poid_data is 0')

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.log.logger.debug")
    def test_update_poid_attribute_on_nodes__successful(self, mock_debug, *_):
        node_poid_data = {"node1": "12345", "node2": "23456"}
        node1 = Mock(node_id="node1", poid="")
        node2 = Mock(node_id="node2", poid="23456")
        node_pool_mgr.cached_nodes_list = [node1, node2]

        failed_nodes = nodemanager_helper_methods.update_poid_attribute_on_nodes(node_poid_data)

        self.assertEqual(failed_nodes, 0)
        self.assertEqual([node.poid for node in node_pool_mgr.cached_nodes_list], ["12345", "23456"])
        self.assertTrue(node1._persist_with_mutex.called)
        self.assertFalse(node2._persist_with_mutex.called)
        self.assertTrue(call("Update operation complete on 2 nodes. Failures: 0") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.log.logger.debug")
    def test_update_poid_attribute_on_nodes__handles_error_while_persisting_node(self, mock_debug, *_):

        node_poid_data = {"node1": "12345", "node2": "23456"}
        node1 = Mock(node_id="node1", poid="")
        node2 = Mock(node_id="node2", poid="23456")
        node1._persist_with_mutex.side_effect = Exception("some_error")
        node_pool_mgr.cached_nodes_list = [node1, node2]

        failed_nodes = nodemanager_helper_methods.update_poid_attribute_on_nodes(node_poid_data)

        self.assertEqual(failed_nodes, 1)
        self.assertEqual([node.poid for node in node_pool_mgr.cached_nodes_list], ["12345", "23456"])
        self.assertTrue(node1._persist_with_mutex.called)
        self.assertFalse(node2._persist_with_mutex.called)
        self.assertTrue(call("Failed to update node node1 - some_error") in mock_debug.mock_calls)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.log.logger.debug")
    def test_update_poid_attribute_on_nodes__handles_nodes_in_pool_but_not_in_enm(self, mock_debug, *_):
        node_poid_data = {"node1": "12345", "node2": "23456"}
        node1 = Mock(node_id="node1", poid="")
        node2 = Mock(node_id="node2", poid="")
        node3 = Mock(node_id="node3", poid="")
        node_pool_mgr.cached_nodes_list = [node1, node2, node3]

        failed_nodes = nodemanager_helper_methods.update_poid_attribute_on_nodes(node_poid_data)

        self.assertEqual(failed_nodes, 1)
        self.assertEqual([node.poid for node in node_pool_mgr.cached_nodes_list], ["12345", "23456", ""])
        self.assertTrue(node1._persist_with_mutex.called)
        self.assertTrue(node2._persist_with_mutex.called)
        self.assertFalse(node3._persist_with_mutex.called)
        self.assertTrue(call("Node node3 in workload pool not listed in POID data (on ENM)") in mock_debug.mock_calls)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.remove')
    def test_reset_nodes__resets_network_values(self, mock_remove):
        msg = nodemanager_helper_methods.reset_nodes(reset_network_values=True)
        self.assertEqual(2, mock_remove.call_count)
        self.assertEqual('\x1b[96m\n  All persisted network values reset.\n\x1b[0m', msg)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get', return_value=10)
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.reset')
    def test_reset_nodes__resets_pool(self, mock_reset, _):
        msg = nodemanager_helper_methods.reset_nodes(reset_network_values=False, no_ansi=False)
        self.assertEqual(1, mock_reset.call_count)
        self.assertEqual('\x1b[96m\n  All 10 nodes reset in the pool\n\x1b[0m', msg)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get', return_value=10)
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.reset')
    def test_reset_nodes__resets_pool_no_ansi(self, mock_reset, _):
        msg = nodemanager_helper_methods.reset_nodes(reset_network_values=False, no_ansi=True)
        self.assertEqual(1, mock_reset.call_count)
        self.assertEqual('\n  All 10 nodes reset in the pool\n', msg)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.has_key', return_value=True)
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.set')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get')
    def test_update_total_node_count__success(self, mock_get, mock_set, _):
        nodemanager_helper_methods.update_total_node_count(update=False)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_set.call_count, 0)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.has_key', return_value=False)
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.get_pool')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.set')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get')
    def test_update_total_node_count__updates_count(self, mock_get, mock_set, mock_pool, _):
        mock_pool._nodes.return_value = {'ERBS': ['Node'] * 2, "RadioNode": ['Node'] * 3}
        nodemanager_helper_methods.update_total_node_count(update=True)
        self.assertEqual(mock_pool.return_value.update_node_ids.call_count, 1)
        self.assertEqual(mock_set.call_count, 1)
        self.assertEqual(mock_get.call_count, 0)

    def test_determine_start_and_end_range__no_range_supplied(self):
        self.assertEqual((None, None), nodemanager_helper_methods.determine_start_and_end_range(None))

    def test_determine_start_and_end_range__start_range_supplied(self):
        self.assertEqual((1, 1), nodemanager_helper_methods.determine_start_and_end_range("1"))

    def test_determine_start_and_end_range__start__and_end_range_supplied(self):
        self.assertEqual((1, 10), nodemanager_helper_methods.determine_start_and_end_range("1-10"))

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.update_cached_list_of_nodes')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persist_node')
    def test_deallocate_profile_from_nodes__removes_profile(self, mock_persist, mock_update_cached_list_of_nodes, _):
        node1 = Mock(node_id="node1", profiles=[])
        node2 = Mock(node_id="node2", profiles=["PROFILE_01"])
        node3 = Mock(node_id="node3", profiles=["PROFILE_02"])
        nodes = [node1, node2, node3]
        nodemanager_helper_methods.deallocate_profile_from_nodes(nodes, "PROFILE_01")
        self.assertEqual(1, mock_persist.call_count)
        mock_update_cached_list_of_nodes.assert_called_with({"node2": node2})

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.update_cached_list_of_nodes')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persist_node')
    def test_deallocate_profile_from_nodes__no_node_updates_needed(
            self, mock_persist, mock_update_cached_list_of_nodes, _):
        node1 = Mock(node_id="node1", profiles=[])
        node2 = Mock(node_id="node2", profiles=["PROFILE_01"])
        node3 = Mock(node_id="node3", profiles=["PROFILE_02"])
        nodes = [node1, node2, node3]
        nodemanager_helper_methods.deallocate_profile_from_nodes(nodes, "PROFILE_03")
        self.assertEqual(0, mock_persist.call_count)
        self.assertFalse(mock_update_cached_list_of_nodes.called)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.default_db')
    def test_persist_node__success(self, mock_db, mock_mutex):
        node = Mock(node_id="Node")
        nodemanager_helper_methods.persist_node(node)
        mock_mutex.assert_called_with("persist-Node", persisted=True)
        mock_db.return_value.set.assert_called_with(node.node_id, node, -1, log_values=False)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.config.get_redis_db_index")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.get_pool")
    def test_select_all_nodes_from_redis__is_successful(self, mock_get_pool, *_):
        node1 = Mock()
        node2 = Mock()
        mock_get_pool.return_value.node_dict = {"ERBS": {"node1": node1}, "RadioNode": {"node2": node2}}
        self.assertEqual([node1, node2], nodemanager_helper_methods.select_all_nodes_from_redis())

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.select_all_nodes_from_redis")
    def test_update_cached_nodes_list__successful(self, mock_select_all_nodes_from_redis, _):
        nodemanager_helper_methods.update_cached_nodes_list()
        self.assertEqual(node_pool_mgr.cached_nodes_list, mock_select_all_nodes_from_redis.return_value)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_manager.ProfileManager")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_properties_manager.ProfilePropertiesManager")
    def test_get_profile_object_from_profile_manager__is_successful(
            self, mock_profilepropertiesmanager, mock_profilemanager):
        profile_object = Mock()
        mock_profilepropertiesmanager.return_value.get_profile_objects.return_value = [profile_object]
        nodemanager_helper_methods.get_profile_object_from_profile_manager("some_profile")
        mock_profilepropertiesmanager.assert_called_with(["some_profile"])
        mock_profilemanager.assert_called_with(profile_object)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.persistence.get")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_manager.ProfileManager")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_properties_manager.ProfilePropertiesManager")
    def test_get_profile_object_from_profile_manager__retrieves_object_from_persistence_if_node_allocation_attrs(
            self, mock_profilepropertiesmanager, mock_profilemanager, mock_get):
        profile_object = Mock()
        delattr(profile_object, 'NUM_NODES')
        delattr(profile_object, 'SUPPORTED_NODE_TYPES')
        mock_profilepropertiesmanager.return_value.get_profile_objects.return_value = [profile_object]
        mock_get.return_value = profile_object
        nodemanager_helper_methods.get_profile_object_from_profile_manager("some_profile")
        mock_profilepropertiesmanager.assert_called_with(["some_profile"])
        mock_get.assert_called_with("some_profile")
        mock_profilemanager.assert_called_with(profile_object)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.persistence.get")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_manager.ProfileManager")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_properties_manager.ProfilePropertiesManager")
    def test_get_profile_object_from_profile_manager__profile_values_supplied(
            self, mock_profilepropertiesmanager, mock_profilemanager, mock_get):
        profile_object = Mock()
        delattr(profile_object, 'NUM_NODES')
        delattr(profile_object, 'SUPPORTED_NODE_TYPES')
        mock_profilepropertiesmanager.return_value.get_profile_objects.return_value = [profile_object]
        mock_get.return_value = profile_object
        nodemanager_helper_methods.get_profile_object_from_profile_manager(
            "some_profile", profile_values={'NUM_NODES': {"ERBS": -1}})
        mock_profilepropertiesmanager.assert_called_with(["some_profile"])
        self.assertEqual(0, mock_get.call_count)
        mock_profilemanager.assert_called_with(profile_object)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.persistence.get")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_manager.ProfileManager")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.profile_properties_manager.ProfilePropertiesManager")
    def test_get_profile_object_from_profile_manager__profile_default_nodes_value_supplied(
            self, mock_profilepropertiesmanager, mock_profilemanager, mock_get):
        profile_object = Mock()
        delattr(profile_object, 'NUM_NODES')
        delattr(profile_object, 'SUPPORTED_NODE_TYPES')
        delattr(profile_object, 'DEFAULT_NODES')
        mock_profilepropertiesmanager.return_value.get_profile_objects.return_value = [profile_object]
        mock_get.return_value = profile_object
        nodemanager_helper_methods.get_profile_object_from_profile_manager(
            "some_profile", profile_values={'DEFAULT_NODES': {"ERBS": {"some_node"}}})
        mock_profilepropertiesmanager.assert_called_with(["some_profile"])
        self.assertEqual(0, mock_get.call_count)
        mock_profilemanager.assert_called_with(profile_object)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.DEALLOCATION_IN_PROGRESS", None)
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.threading.current_thread")
    def test_set_deallocation_in_progress__returns_none_if_flag_not_set(self, mock_current_thread):
        mock_current_thread.return_value.name = "some_thread"
        self.assertIsNone(nodemanager_helper_methods.set_deallocation_in_progress("profile_1"))
        self.assertEqual(nodemanager_helper_methods.DEALLOCATION_IN_PROGRESS, "some_thread_profile_1")

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.DEALLOCATION_IN_PROGRESS", "some_other_thread")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.threading.current_thread")
    def test_set_deallocation_in_progress__returns_message_if_flag_is_set(self, mock_current_thread):
        self.assertEqual("De-allocation of nodes currently in progress by another process - retry later",
                         nodemanager_helper_methods.set_deallocation_in_progress("profile_2"))
        self.assertFalse(mock_current_thread.called)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.DEALLOCATION_IN_PROGRESS", "some_thread_profile_1")
    def test_set_deallocation_complete__successful(self):
        nodemanager_helper_methods.set_deallocation_complete()
        self.assertEqual(nodemanager_helper_methods.DEALLOCATION_IN_PROGRESS, None)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.deallocate_nodes")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.get_profile_object_from_profile_manager")
    def test_perform_deallocate_actions__successful_when_no_nodes_specified(
            self, mock_get_profile_object_from_profile_manager, mock_deallocate_nodes):
        nodemanager_helper_methods.perform_deallocate_actions("profile1")
        mock_get_profile_object_from_profile_manager.assert_called_with("profile1")
        mock_deallocate_nodes.assert_called_with(mock_get_profile_object_from_profile_manager.return_value)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.deallocate_unused_nodes_from_profile")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.get_profile_object_from_profile_manager")
    def test_perform_deallocate_actions__successful_when_nodes_specified(
            self, mock_get_profile_object_from_profile_manager, mock_deallocate_unused_nodes_from_profile):
        node1, node2, node3 = Mock(node_id="Node1"), Mock(node_id="Node2"), Mock(node_id="Node3")
        node_pool_mgr.cached_nodes_list = [node1, node2, node3]
        nodes = "Node1,Node2"
        nodemanager_helper_methods.perform_deallocate_actions("profile1", nodes)
        self.assertFalse(mock_get_profile_object_from_profile_manager.called)
        mock_deallocate_unused_nodes_from_profile.assert_called_with([node1, node2], "profile1")

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.config.set_prop")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.deallocate_profile_from_nodes")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.get_profile_object_from_profile_manager")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.allocate_nodes")
    def test_allocate_nodes__is_successful_if_nodes_not_specified(
            self, mock_allocate_nodes, mock_get_profile_object_from_profile_manager,
            mock_deallocate_profile_from_nodes, mock_set_prop):
        node1 = Mock()
        node_pool_mgr.cached_nodes_list = [node1]
        profile = Mock()
        mock_get_profile_object_from_profile_manager.return_value = profile
        nodemanager_helper_methods.perform_allocation_tasks("PROFILE_01", "", network_config="40k")
        mock_allocate_nodes.assert_called_with(profile, nodes="")
        mock_get_profile_object_from_profile_manager.assert_called_with("PROFILE_01", profile_values=None)
        mock_deallocate_profile_from_nodes.assert_called_with([node1], "PROFILE_01")
        self.assertEqual(1, mock_set_prop.call_count)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.deallocate_profile_from_nodes")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.get_profile_object_from_profile_manager")
    @patch("enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.allocate_nodes")
    def test_allocate_nodes__is_successful_if_nodes_specified(
            self, mock_allocate_nodes, mock_get_profile_object_from_profile_manager,
            mock_deallocate_profile_from_nodes):
        node1, node2, node3 = Mock(node_id="node1"), Mock(node_id="node2"), Mock(node_id="node3")
        node_pool_mgr.cached_nodes_list = [node1, node2, node3]
        profile = Mock()
        mock_get_profile_object_from_profile_manager.return_value = profile
        nodemanager_helper_methods.perform_allocation_tasks("PROFILE_01", "node1,node2")
        mock_allocate_nodes.assert_called_with(profile, nodes=[node1, node2])
        mock_get_profile_object_from_profile_manager.assert_called_with("PROFILE_01", profile_values=None)
        mock_deallocate_profile_from_nodes.assert_called_with([node1, node2, node3], "PROFILE_01")

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.get_profile_object_from_profile_manager")
    def test_allocate_nodes__raises_runtimeerror_if_profile_name_not_supplied(
            self, mock_get_profile_object_from_profile_manager):
        self.assertRaises(RuntimeError, nodemanager_helper_methods.perform_allocation_tasks, "", "")
        self.assertFalse(mock_get_profile_object_from_profile_manager.called)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.convert_enm_user")
    def test_convert_mos_to_dictionary__converts_users(self, mock_convert_user):
        mo = Mock(name="Name", attrs={"attr": "value"}, user="user")
        key = (u'key',)
        mos = {key: {key: {key: {key: {key: {u'GeranCellRelation4': [mo]}}}}}}
        nodemanager_helper_methods.convert_mos_to_dictionary(mos)
        self.assertEqual(1, mock_convert_user.call_count)
        mock_convert_user.assert_called_with(mo.__dict__)

    @patch("enmutils_int.lib.services.nodemanager_helper_methods.convert_enm_user")
    def test_convert_mos_to_dictionary__not_a_dict(self, mock_convert_user):
        key = (u'key',)
        mos = {key: {key: {key: {key: {key: {u'GeranCellRelation4': []}}}}}}
        nodemanager_helper_methods.convert_mos_to_dictionary(mos)
        self.assertEqual(0, mock_convert_user.call_count)

    def test_convert_enm_user__converts_user(self):
        user = Mock()
        result = nodemanager_helper_methods.convert_enm_user({'user': user})
        self.assertIn('username', result.get('user').keys())

    def test_convert_enm_user__no_user(self):
        user = Mock()
        delattr(user, 'password')
        result = nodemanager_helper_methods.convert_enm_user({'user': user})
        self.assertDictEqual({'user': user}, result)

    def test_stringify_keys__no_a_dict(self):
        self.assertIsNone(nodemanager_helper_methods.stringify_keys([]))

    def test_stringify_keys__success(self):
        test_dict = {('A', '1'): {"B": {('C', '1'): ['mo']}}}
        nodemanager_helper_methods.stringify_keys(test_dict)
        self.assertDictEqual({'A|||1': {'B': {'C|||1': ['mo']}}}, test_dict)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persist_and_set_attr_on_node_from_node_id')
    def test_apply_cell_type_to_lte_nodes__only_updates_nodes_with_missing_attribute(self, mock_persist_and_set):
        node, node1 = Mock(node_id="Node"), Mock(node_id="Node1", lte_cell_type='FDD')
        delattr(node, 'lte_cell_type')
        nodes = [node, node1]
        cell_dict = {"TDD": ["Node"], "FDD": ["Node1"]}
        nodemanager_helper_methods.apply_cell_type_to_lte_nodes(nodes, cell_dict)
        self.assertEqual(1, mock_persist_and_set.call_count)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persist_and_set_attr_on_node_from_node_id')
    def test_apply_cell_type_to_lte_nodes__ignores_bsc_values(self, mock_persist_and_set):
        node, node1 = Mock(node_id="Node"), Mock(node_id="Node1", lte_cell_type='FDD')
        delattr(node, 'lte_cell_type')
        nodes = [node, node1]
        cell_dict = {"LARGE_BSC": ["Node"]}
        nodemanager_helper_methods.apply_cell_type_to_lte_nodes(nodes, cell_dict)
        self.assertEqual(0, mock_persist_and_set.call_count)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persist_and_set_attr_on_node_from_node_id')
    def test_apply_cell_type_to_lte_nodes__returns_all_supplied_nodes(self, mock_persist):
        node, node1 = Mock(node_id="Node", lte_cell_type=None), Mock(node_id="Node1", lte_cell_type='FDD')
        mock_persist.return_value = node
        nodes = [node, node1]
        cell_dict = {"TDD": ["Node"], "FDD": ["Node2"]}
        result = nodemanager_helper_methods.apply_cell_type_to_lte_nodes(nodes, cell_dict)
        self.assertEqual(1, mock_persist.call_count)
        self.assertEqual(2, len(result))

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.default_db')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.log.logger.debug')
    def test_persist_and_set_attr_on_node_from_node_id__updates_node_attribute(self, mock_debug, mock_db, _):
        node = Mock(node_id="Node1")
        mock_db.return_value.get.return_value = node
        nodemanager_helper_methods.persist_and_set_attr_on_node_from_node_id(node, "lte_cell_type", "TDD")
        mock_debug.assert_called_with('Updating attribute lte_cell_type on node: Node1.')
        self.assertEqual("TDD", node.lte_cell_type)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.mutexer.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.default_db')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.log.logger.debug')
    def test_persist_and_set_attr_on_node_from_node_id__node_not_found(self, mock_debug, mock_db, _):
        node = Mock(node_id="Node1")
        mock_db.return_value.get.return_value = None
        updated_node = nodemanager_helper_methods.persist_and_set_attr_on_node_from_node_id(
            node, "lte_cell_type", "TDD")
        mock_debug.assert_called_with('Cannot update node attribute, node id: Node1 not found in persistence.')
        self.assertEqual(updated_node.lte_cell_type, "TDD")

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get',
           side_effect=[None, {"FDD": [], "TDD": []}])
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.create_cell_dict')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.apply_cell_type_to_lte_nodes')
    def test_retrieve_cell_information_and_apply_cell_type__creates_cell_dict(self, mock_apply, mock_persist_dict, *_):
        nodemanager_helper_methods.retrieve_cell_information_and_apply_cell_type([])
        self.assertEqual(1, mock_persist_dict.call_count)
        self.assertEqual(1, mock_apply.call_count)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get', return_value={"FDD": [], "TDD": []})
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.create_cell_dict')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.apply_cell_type_to_lte_nodes')
    def test_retrieve_cell_information_and_apply_cell_type__uses_existing_cell_dict(self, mock_apply,
                                                                                    mock_persist_dict, *_):
        nodemanager_helper_methods.retrieve_cell_information_and_apply_cell_type(["Node"], return_updated_nodes=True)
        self.assertEqual(0, mock_persist_dict.call_count)
        self.assertEqual(1, mock_apply.call_count)

    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.mutex')
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get', return_value=None)
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.create_cell_dict', side_effect=RuntimeError("Error"))
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.apply_cell_type_to_lte_nodes')
    def test_retrieve_cell_information_and_apply_cell_type__returns_original_nodes_if_no_cell_dict(
            self, mock_apply, mock_create_dict, *_):
        result = nodemanager_helper_methods.retrieve_cell_information_and_apply_cell_type(
            [], return_updated_nodes=True)
        self.assertEqual(1, mock_create_dict.call_count)
        self.assertEqual(0, mock_apply.call_count)
        self.assertListEqual(result, [])

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.persistence.get',
           side_effect=[None, {"FDD": [], "TDD": []}])
    @patch('enmutils_int.lib.services.nodemanager_helper_methods.node_pool_mgr.persist_dict_value',
           side_effect=[RuntimeError("Error"), None, None])
    def test_create_cell_dict__retrys_if_runtime_error(self, mock_persist_dict, mock_get, _):
        nodemanager_helper_methods.create_cell_dict()
        self.assertEqual(3, mock_persist_dict.call_count)
        self.assertEqual(2, mock_get.call_count)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
