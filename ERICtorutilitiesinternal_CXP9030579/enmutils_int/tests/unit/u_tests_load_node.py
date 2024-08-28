#!/usr/bin/env python
import unittest2
from mock import patch, Mock
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib.exceptions import AddProfileToNodeError, RemoveProfileFromNodeError
from enmutils_int.lib.load_node import (ERBSLoadNode, BaseLoadNode, filter_nodes_having_poid_set, HTTPError,
                                        annotate_fdn_poid_return_node_objects, get_all_enm_network_element_objects,
                                        fetch_latest_node_obj, verify_nodes_against_enm, LoadNodeMixin)
from testslib import unit_test_utils
from testslib.unit_test_utils import get_nodes, get_profile


class LoadNodeUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.load_node.LoadNodeMixin.__init__', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.compare_and_update_persisted_node')
    @patch('enmutils_int.lib.load_node.mutexer.mutex')
    @patch('enmutils_int.lib.load_node.log.logger.debug')
    @patch('enmutils_int.lib.load_node.persistence.get_from_default_db', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_add_profile__successfully_adds_a_profile_to_a_node(self, mock_persist, mock_get_from_db, mock_debug,
                                                                mock_mutex, mock_compare, _):
        mock_compare.return_value = mock_profile = Mock(NAME="test_profile")
        load_node_mix_in = LoadNodeMixin()
        load_node_mix_in.node_id = "test_id"
        load_node_mix_in.profiles = []
        node = load_node_mix_in.add_profile(mock_profile)
        self.assertEqual(["test_profile"], node.profiles)
        mock_persist.assert_called_once_with()
        mock_get_from_db.assert_called_once_with('test_id')
        self.assertFalse(mock_debug.called)
        mock_mutex.assert_called_once_with('persist-test_id', log_output=False)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin.__init__', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.compare_and_update_persisted_node')
    @patch('enmutils_int.lib.load_node.mutexer.mutex')
    @patch('enmutils_int.lib.load_node.log.logger.debug')
    @patch('enmutils_int.lib.load_node.persistence.get_from_default_db', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_add_profile__raises_AddProfileToNodeError_if_a_profile_already_exists_on_a_node(
            self, mock_persist, mock_get_from_db, mock_debug, mock_mutex, mock_compare, _):
        mock_compare.return_value = mock_profile = Mock(NAME="test_profile")
        load_node_mix_in = LoadNodeMixin()
        load_node_mix_in.node_id = "test_id"
        load_node_mix_in.profiles = []
        node = load_node_mix_in.add_profile(mock_profile)
        self.assertEqual(["test_profile"], node.profiles)
        node.profiles.append("test_profile")
        mock_persist.assert_called_once_with()
        mock_get_from_db.assert_called_once_with('test_id')
        self.assertFalse(mock_debug.called)
        self.assertRaises(AddProfileToNodeError, node.add_profile, mock_profile)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin.__init__', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.compare_and_update_persisted_node')
    @patch('enmutils_int.lib.load_node.mutexer.mutex')
    @patch('enmutils_int.lib.load_node.log.logger.debug')
    @patch('enmutils_int.lib.load_node.persistence.get_from_default_db', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_add_profile__adding_an_exclusive_profile_to_a_node_marks_the_node_exclusivity_to_true(
            self, mock_persist, mock_get_from_db, mock_debug, mock_mutex, mock_compare, _):
        mock_compare.return_value = mock_profile = Mock(NAME="test_profile", exclusive=True)
        load_node_mix_in = LoadNodeMixin()
        load_node_mix_in.node_id = "test_id"
        load_node_mix_in.profiles = []
        load_node_mix_in._is_exclusive = True
        node = load_node_mix_in.add_profile(mock_profile)
        self.assertEqual(["test_profile"], node.profiles)
        mock_persist.assert_called_once_with()
        mock_get_from_db.assert_called_once_with('test_id')
        self.assertFalse(mock_debug.called)
        mock_mutex.assert_called_once_with('persist-test_id', log_output=False)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin.__init__', return_value=None)
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.compare_and_update_persisted_node')
    @patch('enmutils_int.lib.load_node.mutexer.mutex')
    @patch('enmutils_int.lib.load_node.log.logger.debug')
    @patch('enmutils_int.lib.load_node.persistence.get_from_default_db')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_add_profile__sets_the_profiles_on_a_node_equal_to_those_profiles_on_the_node_stored_in_persistence(
            self, mock_persist, mock_get_from_db, mock_debug, mock_mutex, mock_compare, _):
        mock_profile = Mock(NAME="test_profile")
        load_node_mix_in = LoadNodeMixin()
        load_node_mix_in.node_id = "test_id"
        load_node_mix_in.profiles = ["test_profile1"]
        mock_get_from_db.return_value = load_node_mix_in
        mock_compare.return_value = load_node_mix_in
        node = load_node_mix_in.add_profile(mock_profile)
        self.assertEqual(["test_profile1", "test_profile"], node.profiles)
        mock_persist.assert_called_once_with()
        mock_get_from_db.assert_called_once_with('test_id')
        self.assertFalse(mock_debug.called)
        mock_mutex.assert_called_once_with('persist-test_id', log_output=False)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_remove_profile_successfully_removes_a_profile_from_a_node(self, mock_persist):
        node = get_nodes(1)[0]
        profile = get_profile(name="FM_03")
        node.add_profile(profile)
        node.remove_profile(profile)
        self.assertTrue(mock_persist.called)
        self.assertEqual(len(node.profiles), 0)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_remove_profile_raises_RemoveProfileFromNodeError_if_a_profile_does_not_exist_on_a_node(self, mock_persist):
        node = get_nodes(1)[0]
        profile = get_profile(name="FM_03")
        self.assertRaises(RemoveProfileFromNodeError, node.remove_profile, profile)
        self.assertTrue(mock_persist.called)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    def test_removing_an_exclusive_profile_from_a_node_marks_the_node_exclusivity_to_false(self, mock_persist):
        node = get_nodes(1)[0]
        profile = get_profile(name="FM_02", exclusive=True)
        node.add_profile(profile)
        self.assertTrue(node._is_exclusive)
        node.remove_profile(profile)
        self.assertFalse(node._is_exclusive)
        self.assertTrue(mock_persist.called)

    @patch('enmutils_int.lib.load_node.LoadNodeMixin._persist')
    @patch('enmutils_int.lib.load_node.persistence.get_from_default_db')
    def test_remove_profile_sets_the_profiles_on_a_node_equal_to_those_profiles_on_the_node_stored_in_persistence(
            self, mock_get_from_default_db, _):
        node1persisted = get_nodes(1)[0]
        node1persisted.profiles.extend(["FM_01", "FM_02", "FM_03"])
        mock_get_from_default_db.return_value = node1persisted
        node1 = get_nodes(1)[0]
        node1.profiles.append("FM_03")
        profile = get_profile(name="FM_03")
        node1.remove_profile(profile)
        self.assertEqual(node1.profiles, node1persisted.profiles)

    def test_is_node_available_to_profile_returns_false_when_profile_in_available_to_profiles(self):
        node = get_nodes(1)[0]
        profile = get_profile(name="FM_01", exclude_nodes_from=['FM_02'])
        self.assertFalse(node.is_pre_allocated_to_profile(profile))

    def test_is_node_available_to_profile_returns_true_when_profile_in_available_to_profiles(self):
        node = get_nodes(1)[0]
        profile = get_profile(name="FM_01", exclude_nodes_from=['FM_02'])
        node.available_to_profiles = set(['FM_01'])
        self.assertTrue(node.is_pre_allocated_to_profile(profile))

    @patch('enmutils_int.lib.load_node.ERBSLoadNode._persist')
    @patch('enmutils_int.lib.load_node.LoadNodeMixin.exclude_nodes_from', side_effect=[True, False])
    def test_is_node_available_returns_false_if_node_has_profile_in_excludes_from_list(self, *_):
        node = get_nodes(1)[0]
        profile1 = get_profile(name="FM_02", exclusive=True)
        node.add_profile(profile1)
        profile2 = get_profile(name="FM_01", exclude_nodes_from=['FM_02'])
        self.assertFalse(node.is_available_for(profile2))

    @patch('enmutils_int.lib.load_node.ERBSLoadNode.exclude_nodes_from', return_value=False)
    def test_is_available_false_if_excluded(self, *_):
        node = ERBSLoadNode(primary_type="ERBS", profiles=[])
        profile = Mock()
        self.assertFalse(node.is_available_for(profile))

    @patch('enmutils_int.lib.load_node.ERBSLoadNode.exclude_nodes_from', return_value=True)
    def test_is_available_for_not_exclusive(self, *_):
        node = ERBSLoadNode(primary_type="ERBS", profiles=[])
        profile = Mock()
        profile.NODE_TYPES_TO_EXCLUDE_FROM = ["ERBS"]
        profile.NAME = "CMSYNC_02"
        profile.EXCLUSIVE = False
        self.assertTrue(node.is_available_for(profile))

    def test_is_available_for_is_exclusive(self):
        node = ERBSLoadNode(primary_type="ERBS", profiles=[], _is_exclusive=True)
        profile = Mock()
        profile.NAME = "CMSYNC_02"
        profile.EXCLUSIVE = True
        delattr(profile, "EXCLUDE_NODES_FROM")
        self.assertTrue(node.is_available_for(profile))

    def test_is_available_for_is_exclusive_not_retained_node(self):
        node = ERBSLoadNode(primary_type="ERBS", profiles=["CMSYNC_04"], _is_exclusive=True)
        profile = Mock()
        profile.NAME = "CMSYNC_02"
        profile.EXCLUSIVE = True
        delattr(profile, "EXCLUDE_NODES_FROM")
        self.assertFalse(node.is_available_for(profile))

    def test_is_available_false_for_if_allocated_to_is_exclusive(self):
        node = ERBSLoadNode(primary_type="ERBS", profiles=['CMIMPORT_02'], _is_exclusive=True)
        profile = Mock()
        profile.NAME = "CMSYNC_02"
        profile.EXCLUSIVE = False
        delattr(profile, "EXCLUDE_NODES_FROM")
        self.assertFalse(node.is_available_for(profile))

    def test_is_available_for_is_exclusive_retained_node(self):
        node = ERBSLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"], _is_exclusive=True)
        profile = Mock()
        profile.NAME = "CMSYNC_02"
        profile.EXCLUSIVE = True
        delattr(profile, "EXCLUDE_NODES_FROM")
        self.assertTrue(node.is_available_for(profile))

    def test_exclude_nodes_filters_correctly(self):
        node = ERBSLoadNode(primary_type="RNC", profiles=["CMSYNC_04"])
        profile = Mock()
        profile.NODE_TYPES_TO_EXCLUDE_FROM = ["ERBS"]
        profile.NAME = "CMSYNC_02"
        profile.EXCLUDE_NODES_FROM = ["CMSYNC_04"]
        self.assertTrue(node.exclude_nodes_from(profile))
        node.primary_type = "ERBS"
        self.assertFalse(node.exclude_nodes_from(profile))
        profile.EXCLUDE_NODES_FROM = ["CMSYNC_06"]
        self.assertTrue(node.exclude_nodes_from(profile))

    @patch('enmutils_int.lib.load_node.ERBSLoadNode._persist')
    def test_reset_clears_profiles_and_exclusivity(self, _):
        node = ERBSLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"], _is_exclusive=True)
        node.reset()
        self.assertEqual(node.profiles, [])
        self.assertFalse(node.is_exclusive)

    @patch('enmutils_int.lib.load_node.BaseLoadNode._persist_with_mutex')
    def test_set_fdn_poid__success(self, _):
        node = BaseLoadNode()
        node.set_fdn_poid('fdn', 'poid')
        self.assertEqual(node.fdn, "fdn")
        self.assertEqual(node.poid, 'poid')

    @patch('enmutils_int.lib.load_node.mutexer.mutex')
    @patch('enmutils_int.lib.load_node.BaseLoadNode._persist')
    def test_persist_with_mutex__calls_persist(self, mock_persist, _):
        node = BaseLoadNode()
        node._persist_with_mutex()
        self.assertEqual(1, mock_persist.call_count)

    @patch('enmutils_int.lib.load_node.persistence.default_db')
    def test_persist__is_successful(self, mock_db):
        node = ERBSLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"], _is_exclusive=True)
        node._persist()
        self.assertEqual(1, mock_db.return_value.set.call_count)

    def test_eq__returns_false_dictionaries_vary(self):
        node = BaseLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"], _is_exclusive=True)
        other_node = Mock()
        self.assertFalse(node.__eq__(other_node))

    def test_eq__returns_true(self):
        node = BaseLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"], _is_exclusive=True)
        self.assertTrue(node.__eq__(node))

    @patch('enmutils_int.lib.load_node.BaseLoadNode.__eq__', return_value=False)
    def test_compare_and_update_persisted_node__updates_persisted_node(self, _):
        node = BaseLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"])
        node1 = BaseLoadNode(primary_type=None, profiles=["CMSYNC_04"])
        node.compare_and_update_persisted_node(node1)
        self.assertEqual(node1.primary_type, "ERBS")
        self.assertListEqual(node1.profiles, ["CMSYNC_04"])

    @patch('enmutils_int.lib.load_node.BaseLoadNode.__eq__', return_value=True)
    def test_compare_and_update_persisted_node__no_update(self, _):
        node = BaseLoadNode(primary_type="ERBS", profiles=["CMSYNC_02"])
        node1 = BaseLoadNode(primary_type=None, profiles=["CMSYNC_04"])
        node.compare_and_update_persisted_node(node1)
        self.assertIsNone(node1.primary_type)

    def test_filter_nodes_having_poid_set__is_successful(self):
        node1 = Mock(poid="123")
        node2 = Mock(poid="")
        nodes = [node1, node2]
        self.assertEqual([node1], filter_nodes_having_poid_set(nodes))

    @patch('enmutils_int.lib.load_node.filter_nodes_having_poid_set')
    def test_annotate_fdn_poid_return_node_objects__calls_filter_nodes(self, mock_filter):
        annotate_fdn_poid_return_node_objects([])
        self.assertEqual(1, mock_filter.call_count)

    def test_get_all_enm_network_element_objects__success(self):
        user, response = Mock(), Mock(ok=True)
        user.get.return_value = response
        self.assertEqual(response, get_all_enm_network_element_objects(user))

    def test_get_all_enm_network_element_objects__raises_http_error(self):
        user, response = Mock(), Mock(ok=False)
        user.get.return_value = response
        self.assertRaises(HTTPError, get_all_enm_network_element_objects, user)

    @patch('enmutils_int.lib.load_node.persistence.get')
    def test_fetch_latest_node_obj_success(self, mock_get):
        node_ids = ["Node"]
        node, node1 = Mock(), Mock()
        node.node_id, node1.node_id = "Node", "Node1"
        nodes = [node, node1]
        fetch_latest_node_obj(node_ids, nodes)
        self.assertEqual(1, mock_get.call_count)

    @patch('enmutils_int.lib.load_node.fetch_latest_node_obj', return_value=[])
    @patch('enmutils_int.lib.load_node.log.logger.debug')
    @patch('enmutils_int.lib.load_node.get_all_enm_network_element_objects')
    def test_verify_nodes_against_enm__success(self, mock_get_objects, mock_debug, _):
        node = Mock()
        node.node_id = "Node"
        mock_get_objects.return_value.json.return_value = [{"moName": "Node", "moType": "type", "poId": "id"}]
        verify_nodes_against_enm([node], Mock())
        mock_debug.assert_called_with("Verifying selected nodes exist in ENM is complete")

    @patch('enmutils_int.lib.load_node.fetch_latest_node_obj', return_value=[])
    @patch('enmutils_int.lib.load_node.log.logger.debug')
    @patch('enmutils_int.lib.load_node.get_all_enm_network_element_objects')
    def test_verify_nodes_against_enm__not_on_enm(self, mock_get_objects, mock_debug, _):
        node = Mock()
        node.node_id = "Node1"
        mock_get_objects.return_value.json.return_value = [{"moName": "Node", "moType": "type", "poId": "id"}]
        verify_nodes_against_enm([node], Mock())
        mock_debug.assert_any_call("WARNING: These nodes don't appear to exist on ENM: ['Node1']")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
