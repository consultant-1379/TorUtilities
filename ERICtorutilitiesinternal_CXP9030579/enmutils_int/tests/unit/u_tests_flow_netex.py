#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils
from enmutils.lib.exceptions import ProfileWarning, EnmApplicationError
from requests.exceptions import HTTPError
from enmutils_int.lib.netex import Collection, Search
from enmutils_int.lib.profile_flows.netex_flows.netex_flow import (Netex01Flow, Netex02Flow, Netex03Flow,
                                                                   Netex04Flow, Netex05Flow, Netex07Flow, NetexCollectionFlow)


class NetexCollectionTestUtils(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.patches = {
            "enmutils_int.lib.profile_flows.netex_flows.netex_flow.get_payload_for_labels": Mock(),
            "enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.NAME": "",
        }
        self.applied_patches = [patch(patch_path, data, create=True) for patch_path, data in self.patches.items()]
        for patch_object in self.applied_patches:
            patch_object.start()

    def tearDown(self):
        patch.stopall()
        unit_test_utils.tear_down()


class NetexCollectionFlowUnitTests(NetexCollectionTestUtils):
    def setUp(self):
        super(NetexCollectionFlowUnitTests, self).setUp()
        self.flow = NetexCollectionFlow()
        self.flow.teardown_list = []

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    def test_cleanup_collections__is_successful_when_collection_in_teardown_list(self, mock_log, mock_chunks):
        mock_cleanup_collection = Mock(spec=Collection(Mock(), "test"))
        mock_cleanup_collection.id = "1"
        self.flow.teardown_list = [mock_cleanup_collection]
        mock_chunks.return_value = [[mock_cleanup_collection]]
        mock_delete_response = mock_cleanup_collection.delete.return_value
        mock_delete_response.json.return_value = [{"id": "1"}]
        mock_delete_response.status_code = 201
        self.flow.cleanup_collections([self.user], mock_cleanup_collection, ["1"])
        self.assertEqual(self.flow.teardown_list, [])
        self.assertEqual(mock_log.logger.debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    def test_cleanup_collections__is_successful_when_collection_not_in_teardown_list(self, mock_log, mock_chunks):
        mock_cleanup_collection = Mock(spec=Collection(Mock(), "test"))
        mock_cleanup_collection.id = "1"
        other_mock = Mock(spec=Collection(Mock(), "othertest"))
        self.flow.teardown_list = [other_mock]
        mock_chunks.return_value = [[mock_cleanup_collection]]
        mock_delete_response = mock_cleanup_collection.delete.return_value
        mock_delete_response.json.return_value = [{"id": "1"}]
        mock_delete_response.status_code = 201
        self.flow.cleanup_collections([self.user], mock_cleanup_collection, ["1"])
        self.assertEqual(mock_log.logger.debug.call_count, 3)
        self.assertEqual(self.flow.teardown_list, [other_mock])

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    def test_cleanup_collections__adds_exception_when_some_colllections_not_deleted(self, mock_debug, mock_chunks):
        mock_cleanup_collection = Mock()
        mock_chunks.return_value = [[mock_cleanup_collection]]
        mock_delete_response = mock_cleanup_collection.delete.return_value
        mock_delete_response.status_code = 200
        mock_delete_response.json.return_value = [{"id": "1"}]
        self.flow.cleanup_collections([self.user], mock_cleanup_collection, ["1"])
        self.assertEqual(mock_debug.call_count, 4)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.search_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections')
    def test_cleanup_collections_based_on_type__is_successful_when_leaf(self, mock_cleanup_collections, *_):
        self.flow.cleanup_collections_based_on_type(self.user, "LEAF")
        self.assertEqual(mock_cleanup_collections.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.search_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections')
    def test_cleanup_collections_based_on_type__is_successful_when_branch(self, mock_cleanup_collections, *_):
        self.flow.cleanup_collections_based_on_type(self.user, "BRANCH")
        self.assertEqual(mock_cleanup_collections.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.search_collections', side_effect=HTTPError)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.add_error_as_exception')
    def test_cleanup_collections_based_on_type__adds_exception_when_search_collections_raises_error(self,
                                                                                                    mock_add_error_as_exception,
                                                                                                    mock_cleanup_collections,
                                                                                                    *_):
        self.flow.cleanup_collections_based_on_type(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_cleanup_collections.call_count, 0)

    @patch(
        'enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections_based_on_type',
        return_value=True)
    def test_cleanup_leaf_branch_topology__is_successful(self, mock_cleanup_collections_based_on_type):
        self.flow.cleanup_leaf_branch_topology(Mock())
        self.assertEqual(mock_cleanup_collections_based_on_type.call_count, 3)

    @patch(
        'enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections_based_on_type',
        side_effect=[False, True, True])
    def test_cleanup_leaf_branch_topology__doesnt_cleanup_branch_or_topology_if_cleanup_leaf_is_false(self,
                                                                                                      mock_cleanup_collections_based_on_type):
        self.flow.cleanup_leaf_branch_topology(Mock())
        self.assertEqual(mock_cleanup_collections_based_on_type.call_count, 1)

    @patch(
        'enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections_based_on_type',
        side_effect=[True, False, True])
    def test_cleanup_leaf_branch_topology__doesnt_cleanup_topology_if_cleanup_branch_is_false(self,
                                                                                              mock_cleanup_collections_based_on_type):
        self.flow.cleanup_leaf_branch_topology(Mock())
        self.assertEqual(mock_cleanup_collections_based_on_type.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections')
    def test_delete_collections__is_successful_when_collections_present(self, mock_cleanup_collections,
                                                                        mock_log):
        self.flow.delete_collections([Mock()], self.user)
        self.assertEqual(mock_cleanup_collections.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections')
    def test_delete_collections__is_successful_when_collections_not_present(self, mock_cleanup_collections,
                                                                            mock_log):
        self.flow.delete_collections([], self.user)
        self.assertEqual(mock_cleanup_collections.call_count, 0)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.cleanup_collections',
           side_effect=HTTPError)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.add_error_as_exception')
    def test_delete_collections__adds_exception_when_search_collections_raises_error(self,
                                                                                     mock_add_error_as_exception,
                                                                                     mock_cleanup_collections):
        self.flow.delete_collections([Mock()], self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_cleanup_collections.call_count, 1)

    def test_cleanup_teardown__is_successful(self):
        mock_collection = Mock(spec=Collection(Mock(), "test"))
        mock_search = Mock(spec=Search(Mock(), "test"))
        self.flow.teardown_list = ["test", mock_collection, mock_search]
        self.assertEqual(len(self.flow.teardown_list), 3)
        self.flow.cleanup_teardown()
        self.assertEqual(len(self.flow.teardown_list), 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Search.execute')
    def test_get_poids_from_search__is_successful(self, mock_execute, mock_debug):
        self.flow.COLLECTION_QUERY = "select all nodes"
        mock_execute.return_value = {
            "objects": [{"id": "41161", "type": "MeContext", "targetTypeAttribute": "RadioNode"},
                        {"id": "41140", "type": "MeContext", "targetTypeAttribute": "RadioNode"}]}
        self.assertEqual(self.flow.get_poids_from_search(self.user), ["41161", "41140"])
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.NetexCollectionFlow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Search.execute')
    def test_get_poids_from_search__adds_exception_when_search_raises_error(self, mock_execute, mock_debug,
                                                                            mock_add_error_as_exception):
        self.flow.COLLECTION_QUERY = "select all nodes"
        mock_execute.side_effect = HTTPError
        self.flow.get_poids_from_search(self.user)
        self.assertEqual(mock_debug.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


class Netex02FlowUnitTests(NetexCollectionTestUtils):
    def setUp(self):
        super(Netex02FlowUnitTests, self).setUp()
        self.flow = Netex02Flow()
        self.flow.NUM_COLLECTIONS = 1
        self.flow.SCHEDULE_SLEEP = 1
        self.flow.NODES_PER_COLLECTION = 3
        self.flow.ADDITIONAL_NODES_PER_COLLECTION = 1
        self.flow.USER_ROLES = ["Admin"]
        self.exception = Exception("Netex_02 Exception")

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    def test_execute_flow_environ_error(self, mock_create_profile_users, mock_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_exception.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.delete')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.get_collection_by_id')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.update_collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.get_poids',
           return_value=['1', '2'])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.create',
           return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    def test_execute_flow_success(self, mock_create_profile_users, mock_search, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.NODES_PER_COLLECTION = 1
        self.flow.execute_flow()
        self.assertTrue(mock_search.return_value.save.called)
        self.assertTrue(mock_search.return_value.get_saved_search_by_id.called)
        self.assertTrue(mock_search.return_value._get_saved_searches.called)
        self.assertTrue(mock_search.return_value.delete.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.delete')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.get_collection_by_id')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.update_collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.get_poids',
           return_value=['1', '2'])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.create',
           return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    def test_execute_flow_success_when_search_not_present(self, mock_create_profile_users, mock_search, *_):
        mock_search.return_value.exists = False
        mock_create_profile_users.return_value = [self.user]
        self.flow.NODES_PER_COLLECTION = 1
        self.flow.execute_flow()
        self.assertTrue(mock_search.return_value.save.called)
        self.assertTrue(mock_search.return_value.get_saved_search_by_id.called)
        self.assertTrue(mock_search.return_value._get_saved_searches.called)
        self.assertTrue(mock_search.return_value.delete.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.delete')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.get_collection_by_id')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Collection.update_collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.get_poids',
           return_value=['1', '2'])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.keep_running',
           side_effect=[True, True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.create',
           return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    def test_execute_flow_exception_in_saved_search_flow(self, mock_create_profile_users,
                                                         mock_search, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.NODES_PER_COLLECTION = 1
        mock_search.return_value.save.side_effect = Exception()
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.create')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    def test_execute_flow_creation_exception(self, mock_create_profile_users, create_mock, add_exception_mock, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.NODES_PER_COLLECTION = 1
        create_mock.side_effect = Exception("Error")
        self.flow.execute_flow()
        self.assertTrue(add_exception_mock.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.create')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.delete')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    def test_execute_flow_deletion_exception(self, mock_create_profile_users, delete_mock, add_exception_mock, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.NODES_PER_COLLECTION = 1
        delete_mock.side_effect = Exception("Error")
        self.flow.execute_flow()
        self.assertTrue(add_exception_mock.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection.create')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    def test_create_collection_adds_error_collection_shortfall(self, mock_add_error_as_exception, *_):
        self.flow.NUM_COLLECTIONS = 2
        self.flow.create_collection([Mock()], Mock())
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.flow.NUM_COLLECTIONS = 1
        self.flow.create_collection([Mock()], Mock())
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute')
    def test_create_collection_objects_raises_value_error(self, mock_nodes,
                                                          mock_add_error_as_exception, _):
        self.flow.NUM_COLLECTIONS = 2
        nodes = [Mock(), Mock()]
        mock_nodes.return_value = nodes
        self.flow.create_collection_objects(nodes, [self.user])
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex02Flow.get_nodes_list_by_attribute')
    def test_create_collection_objects_raises_index_error(self, mock_nodes,
                                                          mock_add_error_as_exception, _):
        self.flow.NUM_COLLECTIONS = 2
        nodes = [Mock(), Mock()]
        mock_nodes.return_value = nodes
        self.flow.create_collection_objects(nodes, [])
        self.assertTrue(mock_add_error_as_exception.called)


class Netex01FlowUnitTests(NetexCollectionTestUtils):
    def setUp(self):
        super(Netex01FlowUnitTests, self).setUp()
        self.flow = Netex01Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.NUM_RESULTS_LARGE_COLLECTION = 1
        self.exception = Exception("Some Exception")

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.arguments.get_random_string', return_value="abcdef")
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.assign_users_to_queries')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow._cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.execute_netex_query_flow')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.search_and_save', return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.search_and_create_collection',
           return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.create_profile_users')
    def test_execute_flow(self, mock_create_profile_users, mock_search_and_create_collection, mock_search_and_save, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.execute_flow()
        self.assertTrue(mock_search_and_create_collection.called)
        self.assertTrue(mock_search_and_save.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.get_nodes_list_by_attribute',
           return_value=[Mock(), Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.arguments.get_random_string', return_value="abcdef")
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.assign_users_to_queries')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow._cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.search_and_save', return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.search_and_create_collection',
           return_value=(Mock(), Mock()))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.execute_netex_query_flow')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.add_error_as_exception')
    def test_execute_flow_adds_error_on_exception(self, mock_add_error, mock_create_profile_users,
                                                  mock_execute_netex_query_flow, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_execute_netex_query_flow.side_effect = self.exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.add_error_as_exception')
    def test_cleanup__is_successful(self, mock_add_error_as_exception):
        collection = Mock()
        collection.id = "1235"
        search = Mock()
        search.id = "1234"
        self.flow.teardown_list = [collection]
        self.flow._cleanup(collection, search)
        self.assertEqual(collection.delete.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.add_error_as_exception')
    def test_cleanup__adds_exception_when_there_is_error(self, mock_add_error_as_exception):
        collection = Mock()
        collection.id = "1235"
        search = Mock()
        search.id = "1234"
        collection.delete.side_effect = self.exception
        search.delete.side_effect = self.exception
        self.flow.teardown_list = [collection]
        self.flow._cleanup(collection, search)
        self.assertEqual(collection.delete.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 2)
        self.assertIsInstance(mock_add_error_as_exception.call_args[0][0], EnmApplicationError)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex01Flow.add_error_as_exception')
    def test_cleanup_performs_no_action_if_ids_not_set(self, mock_add_error):
        collection = Mock()
        collection.id = None
        search = Mock()
        search.id = None
        self.flow._cleanup(collection, search)
        self.assertEqual(collection.delete.call_count, 0)
        self.assertEqual(search.delete.call_count, 0)
        self.assertEqual(mock_add_error.call_count, 0)

    def test_assign_users_to_queries(self):
        self.flow.QUERY_TO_USERS = [["Query", 2, 4], ["Query1", 3, 2], ["Query2", 1, 1]]
        self.flow.assign_users_to_queries(range(15))
        self.assertEqual(len(self.flow.QUERY_TO_USERS[0][3]), 4)
        self.assertEqual(len(self.flow.QUERY_TO_USERS[1][3]), 2)
        self.assertEqual(len(self.flow.QUERY_TO_USERS[2][3]), 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.random.shuffle')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.NetexFlow')
    def test_execute_netex_query_flow__is_successful(self, mock_netex_flow, *_):
        self.flow.QUERY_TO_USERS = [["Query", 1, 1, [Mock(), Mock()]]]
        self.flow.execute_netex_query_flow(self.flow, Mock(), Mock(), Mock())
        self.assertEqual(mock_netex_flow.return_value.execute_flow.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.random.shuffle')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.NetexFlow')
    def test_execute_netex_query_flow__no_users(self, mock_netex_flow, *_):
        self.flow.QUERY_TO_USERS = [["Query", 1, 1, []]]
        self.flow.execute_netex_query_flow(self.flow, Mock(), Mock(), Mock())
        self.assertEqual(mock_netex_flow.return_value._navigate_netex_app_help.call_count, 0)
        self.assertEqual(mock_netex_flow.return_value.execute_flow.call_count, 0)


class Netex03FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = Netex03Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.EXPECTED_NUM_LOCKED_CELLS = 1
        self.flow.NETEX_KTT_TIME_LIMIT = 1
        self.exception = Exception("Some Exception")

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_success_when_cells_match(self, mock_create_profile_users,
                                                   mock_sleep, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 1 instance(s) found', '1 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response]
        self.flow.execute_flow()
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    def test_execute_timed_query__success(self, mock_search, *_):
        mock_search.return_value = Mock()
        self.flow.execute_timed_query(mock_search, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.persistence')
    def test_remove_persistence_value__success(self, mock_persistence):
        self.flow.remove_persistence_value()
        self.assertTrue(mock_persistence.remove.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.persistence')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    def test_execute_timed_query__to_establish(self, mock_search, mock_persistence, *_):
        mock_search.return_value = Mock()
        mock_persistence = Mock()
        setattr(mock_persistence, 'NETEX_03_re_establish', 0.1)
        self.flow.execute_timed_query(mock_search, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_success_when_locked_cells_are_less(self, mock_create_profile_users,
                                                             mock_sleep, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response, response]
        self.flow.execute_flow()
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_index_error_when_locked_cells_are_less(self, mock_create_profile_users,
                                                                        mock_sleep, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        self.flow.EXPECTED_NUM_LOCKED_CELLS = 4
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response]
        self.flow.execute_flow()
        self.assertEqual(mock_add_error_as_exception.call_count, 2)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_script_error_when_locked_cells_are_less(self, mock_create_profile_users,
                                                                         mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response, response]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_exception_when_locked_cells_are_less_during_get_fdns(self, mock_create_profile_users,
                                                                                      mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            Exception]
        self.user.enm_execute.side_effect = [response, ""]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_exception_when_locked_cells_are_less_during_locking(self, mock_create_profile_users,
                                                                                     mock_sleep,
                                                                                     mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6'],
            Exception]
        self.user.enm_execute.side_effect = [response, response, Exception]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_success_when_locked_cells_are_more(self, mock_create_profile_users,
                                                             mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 2 instance(s) found', '2 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_script_error_when_locked_cells_are_more_during_get_fdns(self,
                                                                                         mock_create_profile_users,
                                                                                         mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 2 instance(s) found', '2 instance(s)'],
            []]
        self.user.enm_execute.side_effect = [response, response]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_script_error_when_locked_cells_are_more_during_unlocking(self,
                                                                                          mock_create_profile_users,
                                                                                          mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 2 instance(s) found', '2 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6'],
            Exception]
        self.user.enm_execute.side_effect = [response, response, Exception]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_exception_when_locked_cells_are_more(self, mock_create_profile_users,
                                                                      mock_sleep, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 2 instance(s) found', '2 instance(s)'],
            Exception,
            Exception]
        self.user.enm_execute.side_effect = [response, Exception, Exception]
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_exception_when_number_of_instances_not_present(self, mock_create_profile_users,
                                                                                mock_sleep, mock_add_error_as_exception,
                                                                                *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['abc', 'xyz)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6'],
            Exception]
        self.user.enm_execute.side_effect = [response, response, Exception]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_exception_when_getting_number_of_cells(self, mock_create_profile_users,
                                                                        mock_sleep, mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6'],
            Exception]
        self.user.enm_execute.side_effect = [Exception, Exception, Exception]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_exception_when_executing_search_query(self, mock_create_profile_users,
                                                                       mock_sleep, mock_add_error_as_exception,
                                                                       mock_search_execute, *_):
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 1 instance(s) found', '1 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response]
        mock_search_execute.side_effect = Exception
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.adjust_num_cells')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_enm_error_when_executing_search_query(self, mock_create_profile_users,
                                                                       mock_sleep, mock_add_error_as_exception,
                                                                       mock_search_execute, *_):
        response1 = {u'attributes': [u'administrativeState'], u'objects': [],
                     u'attributeMappings': [{u'attributeNames': [u'administrativeState'],
                                             u'moType': u'EUtranCellFDD'}],
                     u'metadata': {u'SORTABLE': True, u'INFO_MESSAGE': 0,
                                   u'MAX_UI_CACHE_SIZE': 100000,
                                   u'RESULT_SET_TOTAL_SIZE': 1050}}
        mock_create_profile_users.return_value = [self.user]
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 1 instance(s) found', '1 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response]
        mock_search_execute.return_value = response1
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.__init__', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.Search.execute')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.adjust_num_cells')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex03Flow.create_profile_users')
    def test_execute_flow_raises_environ_error_when_not_enough_cells(self, mock_create_profile_users,
                                                                     mock_sleep, mock_exceptions,
                                                                     mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [self.user]
        mock_exceptions.return_value = 3
        response = Mock()
        response.get_output.side_effect = [
            ['EUtranCellFDD 0 instance(s) found', '0 instance(s)'],
            [
                'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE03ERBS00027,ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00027-6']]
        self.user.enm_execute.side_effect = [response, response, response]
        self.flow.execute_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)


class Netex04FlowUnitTests(NetexCollectionTestUtils):

    def setUp(self):
        super(Netex04FlowUnitTests, self).setUp()
        self.flow = Netex04Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.exception = Exception("Some Exception")

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.arguments.get_random_string', return_value="abc")
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.create_profile_users')
    def test_execute_flow__is_successful(self, mock_create_profile_users, mock_create_and_execute_threads, *_):
        mock_create_profile_users.return_value = [Mock()]
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_execute_threads.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.arguments.get_random_string', return_value="abc")
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.create_profile_users')
    def test_execute_flow__adds_exception_when_file_not_created(self, mock_create_profile_users,
                                                                mock_create_and_execute_threads,
                                                                mock_collection,
                                                                mock_add_error_as_exception, *_):
        mock_create_profile_users.return_value = [Mock()]
        mock_collection.return_value.create_file.side_effect = Exception
        self.flow.execute_flow()
        self.assertFalse(mock_create_and_execute_threads.called)
        self.assertTrue(mock_add_error_as_exception.called)

    def test_delete__is_successful_when_collection_in_teatdown_list(self):
        mock_collection = Mock()
        mock_collection.return_value.delete.side_effect = None
        self.flow.teardown_list = [mock_collection]
        self.flow.delete(mock_collection)
        self.assertEqual(mock_collection.delete.call_count, 1)

    def test_delete__is_successful_when_collection_not_in_teardown_list(self):
        mock_collection = Mock()
        mock_collection.return_value.delete.side_effect = None
        self.flow.delete(mock_collection)
        self.assertEqual(mock_collection.delete.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex04Flow.add_error_as_exception')
    def test_delete__adds_exception_when_delete_raises_exception(self, mock_add_error_as_exception):
        mock_collection = Mock()
        mock_collection.delete.side_effect = Exception("Exception")
        self.flow.teardown_list = [mock_collection]
        self.flow.delete(mock_collection)
        self.assertEqual(mock_collection.delete.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_task_set_is_successful__for_create_from_file(self):
        collection, profile = Mock(), Mock()
        collection.name = "0"
        profile.teardown_list = []
        self.flow.task_set(collection, profile)
        self.assertEqual(profile.create_from_file.call_count, 1)
        self.assertEqual(profile.update_from_file.call_count, 0)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    def test_task_set_is_successful__for_update_from_file(self, _):
        collection, profile = Mock(), Mock()
        collection.name = "1"
        profile.teardown_list = []
        self.flow.task_set(collection, profile)
        self.assertEqual(profile.create_from_file.call_count, 0)
        self.assertEqual(profile.update_from_file.call_count, 1)

    def test_task_set_logs_exception__for_create_from_file(self):
        collection, profile = Mock(), Mock()
        collection.name = "0"
        profile.teardown_list = []
        profile.create_from_file.side_effect = self.exception
        self.flow.task_set(collection, profile)
        self.assertEqual(profile.create_from_file.call_count, 1)
        self.assertTrue(profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    def test_task_set_logs_exception__for_update_from_file(self, _):
        collection, profile = Mock(), Mock()
        collection.name = "1"
        profile.update_from_file.side_effect = self.exception
        profile.teardown_list = []
        self.flow.task_set(collection, profile)
        self.assertEqual(profile.update_from_file.call_count, 1)
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertIn(collection, profile.teardown_list)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    def test_create_from_file__is_successful(self, mock_debug, *_):
        worker = Mock()
        profile = Mock()
        worker.exists = False
        self.flow.create_from_file(worker, profile)
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    def test_create_from_file__raises_profile_warning(self, mock_debug, *_):
        worker = Mock()
        profile = Mock()
        worker.exists = True
        with self.assertRaises(ProfileWarning):
            self.flow.create_from_file(worker, profile)
            self.assertEqual(mock_debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    def test_update_from_file__is_successful(self, mock_debug, *_):
        worker = Mock()
        worker.exists = True
        self.flow.update_from_file(worker)
        self.assertEqual(mock_debug.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    def test_update_from_file__raises_profile_warning(self, mock_debug, *_):
        worker = Mock()
        worker.exists = False
        with self.assertRaises(ProfileWarning):
            self.flow.update_from_file(worker)
            self.assertEqual(mock_debug.call_count, 1)


class Netex05FlowUnitTests(NetexCollectionTestUtils):

    def setUp(self):
        super(Netex05FlowUnitTests, self).setUp()
        self.flow = Netex05Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.NUM_BRANCH_COLLECTIONS = 2
        self.flow.NUM_LEAF_COLLECTIONS = 1
        self.flow.NUM_ELEMENTS_IN_COLLECTION = 1
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.SLEEP_TIME_BEFORE_CLEANUP = 0
        self.flow.teardown_list = []

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup_teardown')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.'
           'create_and_traverse_topology_and_collections')
    def test_execute_flow__is_successful(self, mock_create_and_traverse_topology_and_collections, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_create_and_traverse_topology_and_collections.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.traverse_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_regular_collections_for_leaf')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_branch_collections',
           return_value=([Mock()], 1))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup')
    def test_create_and_traverse_topology_and_collections__is_successful(self, mock_cleanup, *_):
        self.flow.create_and_traverse_topology_and_collections([self.user], 0)
        self.assertTrue(mock_cleanup.called)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.traverse_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_regular_collections_for_leaf')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_branch_collections',
           return_value=([Mock()], 1))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_root_custom_topology',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_create_and_traverse_topology_and_collections__adds_exception_when_no_root_topology(self,
                                                                                                mock_add_error_as_exception,
                                                                                                *_):
        self.flow.create_and_traverse_topology_and_collections([self.user], 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.traverse_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_regular_collections_for_leaf')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_branch_collections',
           return_value=([], None))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_create_and_traverse_topology_and_collections__adds_exception_when_no_branch_collections(self,
                                                                                                     mock_add_error_as_exception,
                                                                                                     *_):
        self.flow.create_and_traverse_topology_and_collections([self.user], 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.traverse_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_regular_collections_for_leaf',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_branch_collections',
           return_value=([Mock()], 1))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_create_and_traverse_topology_and_collections__adds_exception_when_no_leaf_collections(self,
                                                                                                   mock_add_error_as_exception,
                                                                                                   *_):
        self.flow.create_and_traverse_topology_and_collections([self.user], 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.traverse_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_regular_collections_for_leaf')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_branch_collections',
           return_value=([Mock()], 1))
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.create_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_create_and_traverse_topology_and_collections__adds_exception_when_unable_to_retrieve_root_topology_(self,
                                                                                                                 mock_add_error_as_exception,
                                                                                                                 mock_create_root_custom_topology,
                                                                                                                 *_):
        mock_create_root_custom_topology.return_value.get_collection_by_id.side_effect = HTTPError
        self.flow.create_and_traverse_topology_and_collections([self.user], 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_root_custom_topology__is_successful(self, mock_collection, mock_log, _):
        self.assertEqual(self.flow.create_root_custom_topology(self.user), mock_collection.return_value)
        self.assertEqual(mock_collection.return_value.create.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_root_custom_topology__adds_exception_when_unable_to_create_collection(self, mock_collection,
                                                                                          mock_log,
                                                                                          mock_add_error_as_exception,
                                                                                          _):
        mock_collection.return_value.create.side_effect = HTTPError
        self.flow.create_root_custom_topology(self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_branch_collections__is_successful(self, mock_collection, mock_log, _):
        mock_collection_obj = mock_collection.return_value
        mock_collection_obj.id = "2"
        self.assertEqual(self.flow.create_branch_collections(self.user, "1", 2),
                         ([mock_collection_obj, mock_collection_obj], "2"))
        self.assertEqual(mock_collection.return_value.create.call_count, 2)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_branch_collections__adds_exception_when_unable_to_create_collection(self, mock_collection,
                                                                                        mock_log,
                                                                                        mock_add_error_as_exception,
                                                                                        _):
        mock_collection.return_value.create.side_effect = HTTPError
        self.flow.create_branch_collections(self.user, "1", 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_regular_collections_for_leaf__is_successful(self, mock_collection, mock_debug, _):
        self.assertEqual(self.flow.create_regular_collections_for_leaf(self.user, 1),
                         [mock_collection.return_value])
        self.assertEqual(mock_collection.return_value.create.call_count, 1)
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_regular_collections_for_leaf__adds_exception_when_unable_to_create_collection(self,
                                                                                                  mock_create,
                                                                                                  mock_debug,
                                                                                                  mock_add_error_as_exception,
                                                                                                  _):
        mock_create.side_effect = HTTPError
        self.flow.create_regular_collections_for_leaf(self.user, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.search_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.json.loads', return_value=[Mock()])
    def test_traverse_collections__is_successful(self, mock_loads, _):
        mock_root_topology = Mock()
        mock_root_topology.id = "1"
        mock_loads.return_value = [{"id": "1", "name": "test"}]
        self.flow.traverse_collections(self.user, mock_root_topology)
        self.assertEqual(mock_root_topology.get_collection_by_id.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.search_collections', side_effect=HTTPError)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.json.loads', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_traverse_collections__adds_exception_when_search_collections_raises_error(self,
                                                                                       mock_add_error_as_exception,
                                                                                       mock_loads, _):
        mock_root_topology = Mock()
        self.flow.traverse_collections(self.user, mock_root_topology)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_cleanup_branch_collections__is_successful_when_in_teardown_list(self):
        branch_collection = Mock()
        branch_collections = [branch_collection]
        self.flow.teardown_list = branch_collections
        self.flow.cleanup_branch_collections(branch_collections, self.user)
        self.assertEqual(self.flow.teardown_list, [])
        self.assertEqual(branch_collection.delete.call_count, 1)

    def test_cleanup_branch_collections__is_successful_when_not_in_teardown_list(self):
        branch_collection = Mock()
        branch_collections = [branch_collection]
        self.flow.teardown_list = []
        self.flow.cleanup_branch_collections(branch_collections, self.user)
        self.assertEqual(branch_collection.delete.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_cleanup_branch_collections__adds_exception_when_delete_raises_error(self, mock_add_error_as_exception):
        branch_collection = Mock()
        branch_collection.delete.side_effect = Exception
        branch_collections = [branch_collection]
        self.flow.cleanup_branch_collections(branch_collections, self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    def test_cleanup_root_custom_topology__is_successful_when_in_teardown_list(self):
        root_custom_topology = Mock()
        self.flow.teardown_list = [root_custom_topology]
        self.flow.cleanup_root_custom_topology(root_custom_topology, self.user)
        self.assertEqual(self.flow.teardown_list, [])
        self.assertEqual(root_custom_topology.delete.call_count, 1)

    def test_cleanup_root_custom_topology__is_successful_when_not_in_teardown_list(self):
        root_custom_topology = Mock()
        self.flow.teardown_list = []
        self.flow.cleanup_root_custom_topology(root_custom_topology, self.user)
        self.assertEqual(root_custom_topology.delete.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_cleanup_root_custom_topology__adds_exception_when_delete_raises_error(self, mock_add_error_as_exception):
        root_custom_topology = Mock()
        root_custom_topology.delete.side_effect = Exception
        self.flow.cleanup_root_custom_topology(root_custom_topology, self.user)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup_branch_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.delete_collections')
    def test_cleanup__is_successful_when_netex_05(self, mock_delete_collections, mock_cleanup_branch_collections,
                                                  mock_cleanup_root_custom_topology, mock_debug, *_):
        mock_collection = Mock()
        self.flow.NAME = "NETEX_05"
        self.flow.teardown_list = [mock_collection] * 2
        self.flow.cleanup(mock_collection, [mock_collection], [mock_collection], self.user)
        self.assertEqual(mock_delete_collections.call_count, 1)
        self.assertEqual(mock_cleanup_branch_collections.call_count, 1)
        self.assertEqual(mock_cleanup_root_custom_topology.call_count, 1)
        self.assertEqual(mock_debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup_collections_based_on_type')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.cleanup_branch_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.delete_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.add_error_as_exception')
    def test_cleanup__adds_exception_when_error_in_delete_collections(self, mock_add_error_as_exception,
                                                                      mock_delete_collections, mock_debug,
                                                                      mock_cleanup_branch_collections,
                                                                      mock_cleanup_root_custom_topology,
                                                                      mock_cleanup_collections_based_on_type, *_):
        self.flow.NAME = "NETEX_05"
        mock_delete_collections.side_effect = HTTPError
        mock_collection = Mock()
        self.flow.cleanup(mock_collection, [mock_collection], [mock_collection], self.user)
        self.assertEqual(mock_delete_collections.call_count, 1)
        self.assertEqual(mock_cleanup_collections_based_on_type.call_count, 0)
        self.assertEqual(mock_cleanup_branch_collections.call_count, 0)
        self.assertEqual(mock_cleanup_root_custom_topology.call_count, 0)
        self.assertEqual(mock_debug.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


class Netex07FlowUnitTests(NetexCollectionTestUtils):

    def setUp(self):
        super(Netex07FlowUnitTests, self).setUp()
        self.flow = Netex07Flow()
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ["Admin"]
        self.flow.NUM_BRANCH_COLLECTIONS = 1
        self.flow.NUM_LEAF_COLLECTIONS = 1
        self.flow.NUM_ELEMENTS_IN_COLLECTION = 1
        self.flow.SCHEDULE_SLEEP = 0
        self.flow.SLEEP_TIME = 0

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.download_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.cleanup_leaf_branch_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.cleanup_teardown')
    @patch(
        'enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_topology_and_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.import_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.export_collections',
           return_value="test_session_id")
    def test_execute_flow__is_successful(self, mock_export_collections, mock_import_collections,
                                         mock_create_topology_and_collections, mock_cleanup_teardown, *_):
        mock_create_topology_and_collections.return_value = (["1"], Mock(), [Mock()], [Mock()])
        self.flow.execute_flow()
        self.assertEqual(mock_create_topology_and_collections.call_count, 1)
        self.assertEqual(mock_export_collections.call_count, 1)
        self.assertEqual(mock_import_collections.call_count, 1)
        self.assertEqual(mock_cleanup_teardown.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.cleanup')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.download_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.sleep')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.keep_running', side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_profile_users',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.cleanup_leaf_branch_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.cleanup_teardown')
    @patch(
        'enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_topology_and_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.import_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.export_collections',
           return_value="")
    def test_execute_flow__adds_exception_when_no_session_id(self, mock_export_collections, mock_import_collections,
                                                             mock_create_topology_and_collections,
                                                             mock_cleanup_teardown, mock_add_error_as_exception, *_):
        mock_create_topology_and_collections.return_value = (["1"], Mock(), [Mock()], [Mock()])
        self.flow.execute_flow()
        self.assertEqual(mock_create_topology_and_collections.call_count, 1)
        self.assertEqual(mock_export_collections.call_count, 1)
        self.assertEqual(mock_import_collections.call_count, 0)
        self.assertEqual(mock_cleanup_teardown.call_count, 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_required_leaf_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_branch_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_root_custom_topology')
    def test_create_topology_and_collections__is_successful(self, mock_root_custom_topology,
                                                            mock_branch_collections,
                                                            mock_leaf_collections):
        mock_topology = Mock()
        mock_root_custom_topology.return_value = mock_topology
        mock_branch_collections.return_value = [Mock()]
        mock_leaf_collections.return_value = [Mock()]
        self.assertEqual(self.flow.create_topology_and_collections([self.user]), [mock_topology.id])

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_required_leaf_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_branch_collections',
           return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_root_custom_topology',
           return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    def test_create_topology_and_collections__adds_exception_when_no_root_topology(self, mock_add_error_as_exception,
                                                                                   *_):
        self.flow.create_topology_and_collections([self.user])
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_required_leaf_collections')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_branch_collections',
           return_value=[])
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_root_custom_topology')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    def test_create_topology_and_collections__adds_exception_when_no_branch_collections(self,
                                                                                        mock_add_error_as_exception,
                                                                                        *_):
        self.flow.create_topology_and_collections([self.user])
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_branch_collections__is_successful(self, mock_collection, mock_log, _):
        mock_collection_obj = mock_collection.return_value
        mock_collection_obj.id = "2"
        self.assertEqual(self.flow.create_branch_collections(self.user, "1", 1),
                         [mock_collection_obj])
        self.assertEqual(mock_collection.return_value.create.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.log')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Collection')
    def test_create_branch_collections__adds_exception_when_unable_to_create_collection(self, mock_collection, mock_log,
                                                                                        mock_add_error_as_exception, _):
        mock_collection.return_value.create.side_effect = HTTPError
        self.flow.create_branch_collections(self.user, "1", 1)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.chunks')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_regular_collections_for_leaf')
    def test_create_required_leaf_collections__is_successful(self, mock_create_regular_collections_for_leaf, *_):
        self.flow.NUM_LEAF_COLLECTIONS = 3
        mock_collection_obj = Mock()
        mock_create_regular_collections_for_leaf.return_value = [mock_collection_obj]
        self.assertEqual(self.flow.create_required_leaf_collections(self.user, [mock_collection_obj,
                                                                                mock_collection_obj]),
                         [mock_collection_obj])
        self.assertEqual(mock_create_regular_collections_for_leaf.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_regular_collections_for_leaf')
    def test_create_required_leaf_collections__adds_exception_when_unable_to_create_collection(self,
                                                                                               mock_create_regular_collections_for_leaf,
                                                                                               mock_add_error_as_exception,
                                                                                               *_):
        mock_collection_obj = Mock()
        mock_create_regular_collections_for_leaf.return_value = []
        self.flow.create_required_leaf_collections(self.user, [mock_collection_obj])
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex05Flow.get_poids_from_search', return_value=None)
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.create_regular_collections_for_leaf')
    def test_create_required_leaf_collections__raises_enmapplicationerror_when_no_poids(self,
                                                                                        mock_create_regular_collections_for_leaf,
                                                                                        *_):
        self.flow.NUM_LEAF_COLLECTIONS = 1
        mock_collection_obj = Mock()
        mock_create_regular_collections_for_leaf.return_value = [mock_collection_obj]
        with self.assertRaises(EnmApplicationError):
            self.flow.create_required_leaf_collections(self.user, [mock_collection_obj])

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.retrieve_export_collection_status')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.initiate_export_collections')
    def test_export_collections__is_successful(self, mock_initiate_export_collections,
                                               mock_retrieve_export_collection_status, *_):
        self.flow.export_collections(self.user, ["1"])
        self.assertEqual(mock_initiate_export_collections.call_count, 1)
        self.assertEqual(mock_retrieve_export_collection_status.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.retrieve_export_collection_status')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.netex.initiate_export_collections',
           return_value=None)
    def test_export_collections__adds_exception_when_initiate_export_returns_none(self,
                                                                                  mock_initiate_export_collections,
                                                                                  mock_retrieve_export_collection_status,
                                                                                  mock_add_error_as_exception,
                                                                                  *_):
        self.flow.export_collections(self.user, ["1"])
        self.assertEqual(mock_initiate_export_collections.call_count, 1)
        self.assertEqual(mock_retrieve_export_collection_status.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.create_export_dir_and_file')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.download_exported_collections')
    def test_download_collections_is_successful(self, mock_download_exported_collections,
                                                mock_create_export_dir_and_file, _):
        self.flow.download_collections(self.user, "test_session_id", "test_export_file_name")
        self.assertEqual(mock_download_exported_collections.call_count, 1)
        self.assertEqual(mock_create_export_dir_and_file.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.create_export_dir_and_file')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.download_exported_collections', side_effect=HTTPError)
    def test_download_collections_adds_exception_when_http_error(self, mock_download_exported_collections,
                                                                 mock_create_export_dir_and_file,
                                                                 mock_add_error_as_exception, _):
        self.flow.download_collections(self.user, "test_session_id", "test_export_file_name")
        self.assertEqual(mock_download_exported_collections.call_count, 1)
        self.assertEqual(mock_create_export_dir_and_file.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.retrieve_import_collection_status')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.initiate_import_collections')
    def test_import_collections__is_successful(self, mock_initiate_import_collections,
                                               mock_retrieve_import_collection_status, *_):
        self.flow.import_collections(self.user, "test_export_file_name")
        self.assertEqual(mock_initiate_import_collections.call_count, 1)
        self.assertEqual(mock_retrieve_import_collection_status.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.time.time')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.__init__')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.Netex07Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.retrieve_import_collection_status')
    @patch('enmutils_int.lib.profile_flows.netex_flows.netex_flow.initiate_import_collections',
           return_value=None)
    def test_import_collections__adds_exception_when_initiate_import_returns_none(self,
                                                                                  mock_initiate_import_collections,
                                                                                  mock_retrieve_import_collection_status,
                                                                                  mock_add_error_as_exception,
                                                                                  *_):
        self.flow.import_collections(self.user, "test_export_file_name")
        self.assertEqual(mock_initiate_import_collections.call_count, 1)
        self.assertEqual(mock_retrieve_import_collection_status.call_count, 0)
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
