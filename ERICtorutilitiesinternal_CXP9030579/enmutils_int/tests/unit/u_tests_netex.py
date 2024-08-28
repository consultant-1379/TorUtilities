#!/usr/bin/env python
import unittest2
from mock import Mock, patch, mock_open, MagicMock
from requests.exceptions import HTTPError

from enmutils.lib import filesystem
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, EnvironWarning
from enmutils_int.lib.netex import (Collection, NetexFlow, Search, get_all_enm_network_elements,
                                    search_and_create_collection, search_and_save, get_pos_by_poids, initiate_export_collections,
                                    retrieve_export_collection_status, get_all_collections,
                                    search_collections, NETEX_HEADER, JSON_SECURITY_REQUEST,
                                    download_exported_collections, get_status_of_import_collections,
                                    initiate_import_collections, retrieve_import_collection_status,
                                    create_export_dir_and_file, handle_errors_in_retreive_import_collection_status)
from testslib import unit_test_utils

QUERY = "select%20all"


class NetexUnitTests(unittest2.TestCase):
    json_response = [{u'mibRootName': u'netsim_LTE01ERBS00030', u'moName': u'netsimlin537_ERBS0001', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846421'},
                     {u'mibRootName': u'LTE06ERBS00005', u'moName': u'netsimlin537_ERBS0002', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474979073961'},
                     {u'mibRootName': u'netsim_LTE01ERBS00135', u'moName': u'netsimlin537_ERBS0003',
                      u'parentRDN': u'', u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846555'},
                     {u'mibRootName': u'LTE02ERBS00003', u'moName': u'netsimlin537_ERBS0004', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474978060075'},
                     {u'mibRootName': u'netsim_LTE01ERBS00104', u'moName': u'netsimlin537_ERBS0005', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846770'},
                     {u'mibRootName': u'netsim_LTE01ERBS00061', u'moName': u'netsimlin537_ERBS0006', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846494'},
                     {u'mibRootName': u'netsim_LTE01ERBS00001', u'moName': u'netsimlin537_ERBS0007', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846076'},
                     {u'mibRootName': u'netsim_LTE01ERBS00124', u'moName': u'netsimlin537_ERBS0008', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980874415'},
                     {u'mibRootName': u'netsim_LTE01ERBS00138', u'moName': u'netsimlin537_ERBS0009', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846835'},
                     {u'mibRootName': u'netsim_LTE01ERBS00051', u'moName': u'netsimlin537_ERBS0010', u'parentRDN': u'',
                      u'moType': u'NetworkElement', u'attributes': {}, u'poId': u'281474980846287'}]

    json_get_searches_response = [{u"type": u"SavedSearch", u"poId": u"123456789", u"name": u"search1",
                                   u"searchQuery": u"NetworkElement", u"attributes":
                                       {u"category": u"Private", u"userId": u"administrator",
                                        u"name": u"NetworkElement",
                                        u"searchQuery": u"NetworkElement", u"lastUpdated": None,
                                        u"timeCreated": 1464605794227}, u"deletable": True}]

    json_get_collections_response = [{u"name": u"test_collection_1", u"type": u"Collection", u"poId": u"123456789",
                                      u"attributes": {u"category": u"Private", u"userId": u"administrator",
                                                      u"name": u"test_collection_1", u"timeCreated": 1464610384965},
                                      u"deletable": True}]

    fdns_with_FDN_prefix = ['FDN : NetworkElement=netsim_RNC01RBS23',
                            'FDN : SubNetwork=ERBS-SUBNW-1,MeContext=netsim_RNC01RBS23',
                            'FDN : netsim_RNC01RBS23,ManagedElement=1']
    fdns_with_incorrect_prefix = ['dfsa: NetworkElement=netsim_RNC01RBS23', 'ads : NetworkElement=netsim_RNC01RBS22',
                                  'FDNfds : NetworkElement=netsim_RNC01RBS20']

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()
        self.file_name = 'netex_test.txt'
        self.file_path = '/home/enmutils/netex/{0}'.format(self.file_name)
        self.collection = Collection(user=self.user, name="test_collection_1", fdn_file_name=self.file_name)
        self.mock_user = Mock()
        self.profile = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()
        if filesystem.does_file_exist(self.file_path):
            filesystem.delete_file(self.file_path)

    @patch('enmutils_int.lib.netex.Search.execute', return_value={"mo": {"poId": [1, 2]}})
    def test_create_collection__is_successful(self, _):
        nodes = [Mock()]
        collection = Collection(user=self.user, name="test_collection_1", nodes=nodes, parent_ids="1")
        response = Mock(status_code=201)
        response.json.return_value = {"id": "123456789"}
        self.user.post.return_value = response
        try:
            collection.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

        self.assertTrue(collection.id)

    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_create_collection__is_successful_when_poids_are_present(self, mock_debug):
        collection = Collection(user=self.user, name="test_collection_1", poids=["2"])
        response = Mock(status_code=201)
        response.json.return_value = {"id": "123456789"}
        self.user.post.return_value = response
        collection.create()
        self.assertEqual(mock_debug.call_count, 2)
        self.assertTrue(collection.id)

    def test_create_collection__raises_enm_application_error_for_empty_json(self):
        nodes = [Mock()]
        collection = Collection(user=self.user, name="test_collection_1", nodes=nodes)
        response = Mock(status_code=201, ok=True)
        response.json.side_effect = [self.json_response, None]
        self.user.get.return_value = response
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, collection.create)

    def test_cmds_called_three_times_in_def_create_list_of_fdns(self):
        response = Mock()
        response.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.return_value = response
        self.collection.create_list_of_fdns()
        self.assertEqual(3, self.user.enm_execute.call_count)

    def test_create_an_empty_collection_success(self):
        self.collection.user = Mock()
        self.collection.num_results = 1
        self.collection.user.get.return_value.json.return_value = {"objects": [{"id": "1"}]}
        self.collection.user.post.return_value.json.return_value = {"id": "1"}
        self.collection.user.post.return_value.status_code = 201
        try:
            self.collection.create()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))
        self.assertTrue(self.collection.id)

    def test_create_an_empty_collection_raises_http_error(self):
        self.collection.user = Mock()
        self.collection.num_results = 1
        self.collection.user.get.return_value.json.return_value = {"objects": [{"id": "1"}]}
        self.collection.user.post.return_value.json.return_value = {"id": "1"}
        self.collection.user.post.return_value.status_code = 500
        self.collection.user.post.return_value.raise_for_status.side_effect = HTTPError
        self.assertRaises(HTTPError, self.collection.create)

    def test_correct_fdn_added(self):
        response = Mock()
        response.get_output.return_value = self.fdns_with_FDN_prefix
        self.user.enm_execute.return_value = response
        self.assertIn(self.fdns_with_FDN_prefix[0].split('FDN : ')[-1], self.collection.create_list_of_fdns())

    def test_create_list_of_fdns(self):
        response, response1 = Mock(), Mock()
        response.get_output.return_value = self.fdns_with_FDN_prefix
        response1.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.side_effect = [response1, response1, response]
        self.assertIn(self.fdns_with_FDN_prefix[0].split('FDN : ')[-1], self.collection.create_list_of_fdns())

    def test_create_list_of_fdns_key_not_in_line(self):
        response, response1 = Mock(), Mock()
        response.get_output.return_value = self.fdns_with_incorrect_prefix
        response1.get_output.return_value = [u'0 instance(s)']
        self.user.enm_execute.side_effect = [response1, response1, response]
        self.assertNotIn(self.fdns_with_incorrect_prefix[0].split('FDN : ')[-1], self.collection.create_list_of_fdns())

    @patch('enmutils_int.lib.netex.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.netex.Collection.create_list_of_fdns', return_value=["FDN"])
    @patch('enmutils_int.lib.netex.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.netex.filesystem.touch_file')
    def test_create_file(self, mock_touch_file, mock_write_data_to_file, *_):
        self.collection.create_file()
        self.assertTrue(mock_touch_file.called)
        self.assertTrue(mock_write_data_to_file.called)

    @patch('enmutils_int.lib.netex.filesystem.does_file_exist', return_value=True)
    @patch('enmutils_int.lib.netex.Collection.create_list_of_fdns', return_value=[])
    def test_create_file_raises_environ_error(self, *_):
        self.assertRaises(EnvironError, self.collection.create_file)

    @patch('enmutils_int.lib.netex.Collection.create_list_of_fdns', return_value=["FDN"])
    @patch('enmutils_int.lib.netex.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.netex.filesystem')
    def test_create_file_if_does_dir_exist__false(self, mock_filesystem, *_):
        mock_filesystem.does_dir_exist.return_value = False
        self.collection.create_file()
        mock_filesystem.create_dir.assert_called_with('/home/enmutils/netex/')

    @patch('enmutils_int.lib.netex.Collection.create_list_of_fdns', return_value=["FDN"])
    @patch('enmutils_int.lib.netex.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.netex.filesystem.create_dir')
    @patch('enmutils_int.lib.netex.filesystem.does_dir_exist')
    def test_create_file_if_does_dir_exist__true(self, mock_filesystem, mock_create_dir, *_):
        mock_filesystem.return_value = True
        self.collection.create_file()
        self.assertTrue(not mock_create_dir.called)

    @patch('enmutils_int.lib.netex.Collection.create_list_of_fdns', return_value=["FDN"])
    @patch('enmutils_int.lib.netex.filesystem')
    def test_create_file_does_not_add_invalid_fdn(self, mock_fs, *_):
        response = Mock()
        response.get_output.return_value = self.fdns_with_FDN_prefix + self.fdns_with_incorrect_prefix
        self.user.enm_execute.return_value = response
        self.collection.create_file()
        mock_fs.write_data_to_file.assert_called_once_with('FDN', '/home/enmutils/netex/netex_test.txt')

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_create_collection_from_file(self, mock_debug, _):
        response = Mock(status_code=201, ok=True)
        self.user.post.return_value = response
        self.collection.create_collection_from_file()
        self.assertTrue(mock_debug.called)
        self.assertIsNotNone(self.collection.id)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    def test_create_collection_from_file_raises_exception(self, _):
        response = Mock(status_code=404)
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response
        self.assertRaises(HTTPError, self.collection.create_collection_from_file)
        self.assertTrue(response.raise_for_status.called)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_update_collection_from_file(self, mock_debug, _):
        response = Mock(status_code=201, ok=True)
        self.user.put.return_value = response
        self.collection.id = "123456"
        self.collection.update_collection_from_file()
        self.assertTrue(mock_debug.called)

    @patch('__builtin__.open', read_data="data", new_callable=mock_open)
    @patch('enmutils_int.lib.netex.filesystem.does_dir_exist')
    def test_update_collection_from_file_raises_exception(self, *_):
        self.collection.user.put.return_value.status_code = 418
        self.collection.id = "123456"
        self.collection.update_collection_from_file()
        self.assertTrue(self.collection.user.put().raise_for_status.called)

    def test_get_collection_by_id_success(self):
        self.collection.id = "123456"
        response = Mock(status_code=201)
        self.user.get.return_value = response
        try:
            self.collection.get_collection_by_id(self.collection.id, include_contents=True)
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))
        self.assertTrue(self.collection.id)

    def test_get_collection_by_id_success_v2_success(self):
        self.collection.id = "123456"
        self.collection.version = "v2"
        self.collection.user = Mock()
        self.collection.user.get.return_value.status_code = 201
        self.collection.get_collection_by_id(self.collection.id)
        self.assertFalse(self.collection.user.get.return_value.raise_for_status.called)

    def test_get_collection_by_id_success_v2_raises_exception(self):
        self.collection.id = "123456"
        self.collection.version = "v2"
        self.collection.user = Mock()
        self.collection.user.get.return_value.status_code = 404
        self.collection.get_collection_by_id(self.collection.id)
        self.assertTrue(self.collection.user.get.return_value.raise_for_status.called)

    @patch('enmutils_int.lib.netex.log')
    def test_search_collections__is_successful(self, mock_log):
        self.assertEqual(search_collections(self.user), self.user.post.return_value)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.netex.log')
    @patch('enmutils_int.lib.netex.search_collections')
    def test_get_all_collections__is_successful(self, mock_search_collections, mock_log):
        self.assertEqual(get_all_collections(self.user), mock_search_collections.return_value)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils_int.lib.netex.search_collections', side_effect=HTTPError)
    @patch('enmutils_int.lib.netex.log')
    def test_get_all_collections__raises_exception_when_search_gives_http_error(self, mock_log, _):
        with self.assertRaises(HTTPError):
            get_all_collections(self.user)

    def test_update_collection__is_successful(self):
        self.collection.id = "123456"
        self.collection.user = self.user
        get_collection_dict = {"sharing": "public", "sortable": True, "name": "test-collection-1",
                               "timeCreated": 1598454668652, "userId": "test-user", "update": True,
                               "lastUpdated": 1598454668652, "readOnly": False,
                               "contents": [{"attributes": {}, "id": "2"}]}
        self.collection.user.get.return_value.json.return_value = get_collection_dict
        self.collection.user.put.return_value.status_code = 200
        self.collection.update_collection(['1'])
        self.assertFalse(self.collection.user.put.return_value.raise_for_status.called)
        self.assertEqual(self.collection.user.put.call_args[1]["json"],
                         {'isCustomTopology': False, 'sharing': 'public', 'type': 'LEAF', 'name': 'test-collection-1',
                          'contents': [{'attributes': {}, 'id': '1'}]})

    def test_update_collection__raises_exception(self):
        self.collection.id = "123456"
        self.collection.user = self.user
        get_collection_dict = {"sharing": "public", "sortable": True, "name": "test-collection-1",
                               "timeCreated": 1598454668652, "userId": "test-user", "update": True,
                               "lastUpdated": 1598454668652, "readOnly": False,
                               "contents": [{"attributes": {}, "id": "2"}]}
        self.collection.user.get.return_value.json.return_value = get_collection_dict
        self.collection.user.put.return_value.status_code = 404
        self.collection.update_collection(['1'])
        self.assertTrue(self.collection.user.put.return_value.raise_for_status.called)

    def test_get_collection_by_id_raises_http_error(self):
        self.collection.id = "123456"
        response = Mock(status_code=500)
        response.json.return_value = self.json_response
        response.raise_for_status.side_effect = HTTPError()
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.collection.get_collection_by_id, self.collection.id)

    def test_get_collection_by_id_env_error(self):
        response = Mock()
        response.get_output.return_value = []
        self.user.execute.return_value = response
        self.assertRaises(EnvironError, self.collection.get_collection_by_id, None)

    @patch('enmutils_int.lib.netex.Search.execute', return_value={"mo": {"poId": [1, 2]}})
    def test_create_collection_http_error(self, _):
        nodes = [Mock()]
        collection = Collection(user=self.user, name="test_collection_1", nodes=nodes)
        response = Mock(status_code=500)
        response.json.return_value = "123456789"
        response.raise_for_status.side_effect = HTTPError()
        self.user.post.return_value = response
        self.assertRaises(HTTPError, collection.create)

    @patch('enmutils_int.lib.netex.Collection.get_collection_ids_for_delete')
    def test_delete_collection__is_succesful_when_status_code_is_204(self, _):
        collection = Collection(user=self.user, name="test_collection_1")
        collection.user = self.user
        self.user.delete_request.return_value.status_code = 204
        self.assertEqual(collection.delete(collection_ids=["1"]), self.user.delete_request.return_value)

    @patch('enmutils_int.lib.netex.Collection.get_collection_ids_for_delete')
    @patch("enmutils_int.lib.netex.log.logger.debug")
    def test_delete_collection_logs_failure_when_status_code_is_not_204(self, mock_debug, _):
        collection = Collection(user=self.user, name="test_collection_1")
        collection.user = self.user
        self.user.delete_request.return_value.status_code = 200
        collection.delete(collection_ids=["1"])
        self.assertEqual(mock_debug.call_count, 3)
        self.assertTrue("Collection delete failed" in mock_debug.call_args[0][0])

    @patch('enmutils_int.lib.netex.Collection.get_collection_ids_for_delete')
    def test_delete_collection__is_succesful_when_no_collection_ids_in_args_but_id_is_present(self, _):
        collection = Collection(user=self.user, name="test_collection_1")
        collection.id = "1"
        collection.user = self.user
        self.user.delete_request.return_value.status_code = 204
        self.assertEqual(collection.delete(), self.user.delete_request.return_value)

    @patch('enmutils_int.lib.netex.get_all_collections')
    def test_get_collection_ids_for_delete__is_succesful_when_collection_ids_in_args(self, mock_get_all_collections):
        collection = Collection(user=self.user, name="test_collection_1")
        collection.user = self.user
        collection_ids = ["1"]
        self.assertEqual(collection.get_collection_ids_for_delete(collection_ids), collection_ids)
        self.assertEqual(mock_get_all_collections.call_count, 0)

    @patch('enmutils_int.lib.netex.get_all_collections')
    def test_get_collection_ids_for_delete__is_succesful_when_no_collection_ids_in_args_but_id_is_present_and_name_in_search(
            self,
            mock_get_all_collections):
        collection = Collection(user=self.user, name="test_collection_1")
        collection.user = self.user
        mock_get_all_collections.return_value.json.return_value = [{"name": "test_collection_1", "id": "1"}]
        collection.get_collection_ids_for_delete()
        self.assertEqual(mock_get_all_collections.call_count, 1)

    @patch('enmutils_int.lib.netex.get_all_collections')
    def test_get_collection_ids_for_delete__is_succesful_when_no_collection_ids_in_args_but_id_is_present_and_name_not_in_search(
            self,
            mock_get_all_collections):
        collection = Collection(user=self.user, name="test_collection_1")
        collection.user = self.user
        collection.id = "1"
        collection.get_collection_ids_for_delete()
        self.assertEqual(mock_get_all_collections.call_count, 0)

    @patch("enmutils_int.lib.netex.log.logger.debug")
    def test_save_search_success(self, mock_debug):
        user = Mock()
        nodes = [Mock()] * 3
        search = Search(user=user, query="NetworkElement", nodes=nodes)
        user.post.return_value.status_code = 200
        search.save()
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.netex.log.logger.debug")
    def test_get_saved_searches_raises_for_status(self, mock_debug):
        user = Mock()
        user.post.return_value.status_code = 418
        nodes = [Mock()] * 3
        search = Search(user=user, query="NetworkElement", nodes=nodes)
        search._get_saved_searches()
        self.assertTrue(mock_debug.call_count == 0)

    def test_get_saved_search_by_id_success_success(self):
        user = Mock()
        nodes = [Mock()]
        user.get.return_value.status_code = 200
        user.post.return_value.status_code = 200
        user.post.return_value.text = "1"
        search = Search(user=user, query="NetworkElement", nodes=nodes)
        search.save()
        search.get_saved_search_by_id()
        self.assertFalse(user.get.return_value.raise_for_status.called)

    def test_get_saved_search_by_id_raises_exception(self):
        user = Mock()
        nodes = [Mock()]
        user.get.return_value.status_code = 404
        user.post.return_value.status_code = 200
        user.post.return_value.text = "1"
        search = Search(user=user, query="NetworkElement", nodes=nodes)
        search.save()
        search.get_saved_search_by_id()
        self.assertTrue(user.get.return_value.raise_for_status.called)

    def test_save_search_http_error(self):
        user = Mock()
        nodes = [Mock()] * 3
        user.post.return_value.status_code = 503
        user.post.return_value.raise_for_status.side_effect = HTTPError
        search = Search(user=user, query="NetworkElement", nodes=nodes, version="v2")
        self.assertRaises(HTTPError, search.save)

    @patch('enmutils_int.lib.netex.Search.delete')
    def test_teardown_search__success(self, mock_delete):
        nodes = [Mock()]
        search = Search(user=self.user, query="NetworkElement", name="search1", nodes=nodes)
        search._teardown()
        self.assertEqual(mock_delete.call_count, 1)

    def test_query_enm_netex__v2_success(self):
        response = Mock()
        response.status_code = 200
        search = Search(user=self.user, query=QUERY)
        kwargs = {'version': 'v2', 'timeout': 180}
        self.user.get.return_value = response
        search.query_enm_netex(QUERY, self.user, **kwargs)
        self.user.get.assert_called_with('/managedObjects/search/v2?query={0}&'.format(QUERY), headers=NETEX_HEADER,
                                         profile_name=kwargs.get('profile_name'), timeout=180)

    def test_query_enm_netex__v1_success(self):
        response = Mock()
        response.status_code = 200
        search = Search(user=self.user, query=QUERY)
        kwargs = {'version': 'v1', 'timeout': 180}
        self.user.get.return_value = response
        search.query_enm_netex(QUERY, self.user, **kwargs)
        self.user.get.assert_called_with('/managedObjects/query?searchQuery={0}&'.format(QUERY),
                                         profile_name=kwargs.get('profile_name'), headers=JSON_SECURITY_REQUEST)

    def test_query_enm_netex__http_error(self):
        response = Mock()
        response.status_code = 500
        search = Search(user=self.user, query=QUERY)
        kwargs = {'version': 'v1'}
        self.user.get.return_value = response
        search.query_enm_netex(QUERY, self.user, **kwargs)
        self.assertEqual(1, response.raise_for_status.call_count)

    @patch('enmutils_int.lib.netex.Search.query_enm_netex')
    def test_execute__v1_success(self, mock_query):
        response = Mock()
        response.json.return_value = [{'moName': 'id'}]
        mock_query.return_value = response
        search = Search(user=self.user, query=QUERY)
        self.assertDictEqual({'id': {'moName': 'id'}}, search.execute())

    @patch('enmutils_int.lib.netex.Search.query_enm_netex')
    def test_execute__v2_success(self, mock_query):
        response = Mock()
        response.json.return_value = [{'moName': 'id'}]
        mock_query.return_value = response
        search = Search(user=self.user, query=QUERY, version="v2")
        self.assertListEqual(response.json.return_value, search.execute())

    @patch('enmutils_int.lib.netex.Search.query_enm_netex')
    def test_execute__no_match(self, mock_query):
        response, node = Mock(), Mock()
        response.json.return_value = [{'moName': 'id'}]
        node.node_id = "id1"
        mock_query.return_value = response
        search = Search(user=self.user, query=QUERY, nodes=[node])
        self.assertDictEqual({}, search.execute())

    def test_delete_search_success(self):
        nodes = [Mock()]
        search = Search(user=self.user, query="NetworkElement", name="search1", nodes=nodes)
        response = Mock(status_code=200)
        response.json.return_value = self.json_get_searches_response
        self.user.get.return_value = response
        self.user.delete_request.return_value = response

        try:
            search.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_delete_search_success_with_unknown_name(self):
        nodes = [Mock()]
        search = Search(user=self.user, query="NetworkElement", name="unknown", nodes=nodes)
        response = Mock(status_code=200)
        response.json.return_value = self.json_get_searches_response
        self.user.get.return_value = response
        self.user.delete_request.return_value = response

        try:
            search.delete()
        except Exception as e:
            raise AssertionError("Should not have raised error: {}".format(str(e)))

    def test_delete_search_http_error(self):
        nodes = [Mock()]
        search = Search(user=self.user, query="NetworkElement", name="search1", nodes=nodes)
        response = Mock(status_code=500)
        response.raise_for_status.side_effect = HTTPError()
        response.json.return_value = self.json_get_searches_response
        self.user.get.return_value = response
        self.user.delete_request.return_value = response
        search.id = '123456789'
        self.assertRaises(HTTPError, search.delete)

    @patch('enmutils_int.lib.netex.Search.query_enm_netex')
    def test_get_all_enm_network_elements(self, mock_query):
        get_all_enm_network_elements(self.user, fullMo='false').json()
        self.assertEqual(1, mock_query.call_count)

    @patch('enmutils_int.lib.netex.get_all_collections')
    def test_exists__is_successful(self, _):
        self.collection = Collection(user=self.user, name="test_collection_1", fdn_file_name=self.file_name)
        self.collection.user = Mock()
        response = Mock()
        response.status_code = 200
        self.collection.user.get.return_value = response
        self.collection.id = "1234"
        self.assertTrue(self.collection.exists)

    @patch('enmutils_int.lib.netex.get_all_collections')
    def test_exists__true_after_collection_id_not_found(self, mock_get_all_collections):
        mock_user = Mock()
        mock_json = Mock()
        mock_json.status_code = 200
        mock_json.json.return_value = [{"name": "test_collection_1"}]
        mock_get_all_collections.return_value = mock_json
        mock_user.get.side_effect = HTTPError
        self.collection.user = mock_user
        self.collection.id = "1234"
        self.assertTrue(self.collection.exists)

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_exists__false_after_collection_id_none(self, mock_debug, mock_get_all_collections):
        mock_user = Mock()
        mock_json = Mock()
        mock_json.status_code = 200
        mock_json.json.return_value = [{"name": "test_collection_2"}]
        mock_get_all_collections.return_value = mock_json
        self.collection.user = mock_user
        self.collection.id = None
        mock_debug.assert_called("Could not find collection 1234")
        self.assertFalse(self.collection.exists)

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_exists__false_after_collection_id_not_found(self, mock_debug, mock_get_all_collections):
        mock_user = Mock()
        mock_json = Mock()
        mock_json.status_code = 200
        mock_json.json.return_value = [{"name": "test_collection_2"}]
        mock_get_all_collections.return_value = mock_json
        self.collection.user = mock_user
        self.collection.id = "1234"
        mock_debug.assert_called("Could not find collection 1234")
        self.assertFalse(self.collection.exists)

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_exists__raises_enmapplication_error(self, mock_debug, mock_get_all_collections):
        mock_user = Mock()
        mock_json = Mock()
        mock_json.status_code = 401
        mock_get_all_collections.return_value = mock_json
        self.collection.user = mock_user
        self.collection.id = "1234"
        with self.assertRaises(EnmApplicationError) as e:
            self.collection.exists  # pylint: disable=W0104
        self.assertEqual(e.exception.message,
                         "ENM service failed to return a valid response. Response status_code 401, unable "
                         "to get all collections")
        self.assertEqual(mock_debug.call_count, 1)

    @patch('enmutils_int.lib.netex.search_collections')
    def test_delete(self, mock_search_collections):
        response, response1 = Mock(), Mock()
        response1.status_code = 204
        response.json.return_value = [{"name": "test_collection_2"}]
        mock_search_collections.return_value = response
        self.collection.user.delete_request.return_value = response1
        self.collection.delete()

    @patch('enmutils_int.lib.netex.Collection.delete')
    def test_teardown(self, mock_delete):
        self.collection._teardown()
        self.assertEqual(mock_delete.call_count, 1)

    @patch('enmutils_int.lib.netex.get_all_collections')
    def test_delete_does_not_if_no_matching_collection(self, mock_search_collections):
        response, response1 = Mock(), Mock()
        response1.status_code = 204
        response.json.return_value = [{"name": "test_collection_2", "id": "1234"}]
        mock_search_collections.return_value = response
        self.collection.delete()
        self.assertFalse(self.user.delete_request.called)

    def test_get_pos_by_poids_success(self):
        user = Mock()
        get_pos_by_poids(user, poList=["1"])
        self.assertTrue(user.post.called)

    def test_get_pos_by_poids_raises_exception(self):
        user = Mock()
        user.post.return_value.ok = False
        get_pos_by_poids(user, poList=["1"])
        self.assertTrue(user.post.return_value.raise_for_status.called)

    def test_initiate_export_collections_success_when_nested_is_false(self):
        self.mock_user.post.return_value.json.return_value = {"sessionId": "1"}
        initiate_export_collections(self.profile, self.mock_user, [1, 2], nested=False)
        self.assertFalse(self.profile.add_error_as_exception.called)
        self.assertTrue(self.mock_user.post.return_value.json.called)

    def test_initiate_export_collections_success_when_nested_is_true(self):
        self.mock_user.post.return_value.json.return_value = {"sessionId": "1"}
        initiate_export_collections(self.profile, self.mock_user, [1, 2], nested=True)
        self.assertFalse(self.profile.add_error_as_exception.called)
        self.assertTrue(self.mock_user.post.return_value.json.called)

    def test_initiate_export_collections_raises_exception(self):
        self.mock_user.post.side_effect = Exception
        initiate_export_collections(self.profile, self.mock_user, [1, 2])
        self.assertTrue(self.profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.netex.log.logger.debug')
    @patch('enmutils_int.lib.netex.time.sleep')
    def test_retrieve_export_collection_status_success_when_completed(self, mock_sleep, mock_debug):
        self.mock_user.get.return_value.json.return_value = {"status": "COMPLETED_WITH_SUCCESS"}
        retrieve_export_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 3)
        self.assertFalse(self.profile.add_error_as_exception.called)
        self.assertFalse(mock_sleep.called)

    @patch('enmutils_int.lib.netex.log.logger.debug')
    @patch('enmutils_int.lib.netex.time.sleep')
    def test_retrieve_export_collection_status_success_when_in_progress(self, mock_sleep, mock_debug):
        self.mock_user.get.return_value.json.return_value = {"status": "IN_PROGRESS"}
        retrieve_export_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 3)
        self.assertTrue(self.profile.add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.netex.log.logger.debug')
    @patch('enmutils_int.lib.netex.time.sleep')
    def test_retrieve_export_collection_status_raises_exception(self, mock_sleep, mock_debug):
        self.mock_user.get.side_effect = Exception
        retrieve_export_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 2)
        self.assertTrue(self.profile.add_error_as_exception.called)
        self.assertTrue(mock_sleep.called)

    def test_search_exists(self):
        search = Search(user=self.user, query="NetworkElement", name="test")
        response = Mock()
        response.status_code = 200
        response.json.return_value = [{u'searchQuery': u'select MeContext', u'name': u'test',
                                       u'type': u'SavedSearch', u'update': True, u'deletable': True,
                                       u'attributes': {u'category': u'Public', u'searchQuery': u'select MeContext',
                                                       u'name': u'select mecontext',
                                                       u'timeCreated': 1562075189969,
                                                       u'userId': u'netex_02_0702-14462806_u0',
                                                       u'lastUpdated': 1562075189969}, u'poId': u'4505079',
                                       u'delete': True}]
        self.user.get.return_value = response
        self.assertTrue(search.exists)

    def test_search_not_exists(self):
        search = Search(user=self.user, query="NetworkElement", name="test")
        response = Mock()
        response.status_code = 200
        response.json.return_value = [{u'searchQuery': u'select MeContext', u'name': u'wrongtest',
                                       u'type': u'SavedSearch', u'update': True, u'deletable': True,
                                       u'attributes': {u'category': u'Public', u'searchQuery': u'select MeContext',
                                                       u'name': u'wrongtest', u'timeCreated': 1562075189969,
                                                       u'userId': u'netex_02_0702-14462806_u0',
                                                       u'lastUpdated': 1562075189969}, u'poId': u'4505079',
                                       u'delete': True}]
        self.user.get.return_value = response
        self.assertFalse(search.exists)

    def test_download_exported_collections__is_successful(self):
        download_exported_collections(self.mock_user, "test_session_id")
        self.assertEqual(self.mock_user.get.call_count, 1)

    @patch("__builtin__.open", read_data="data", new_callable=mock_open)
    def test_initiate_import_collections__is_successful(self, mock_open):
        self.mock_user.post.return_value.json.return_value = {"sessionId": "1"}
        initiate_import_collections(self.mock_user, "test_file_name")
        self.assertEqual(mock_open.call_count, 1)
        self.assertEqual(self.mock_user.post.return_value.json.call_count, 1)

    def test_get_status_of_import_collections__is_successful(self):
        get_status_of_import_collections(self.mock_user, "test_session_id")
        self.assertEqual(self.mock_user.get.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.netex.log.logger.debug")
    @patch("enmutils_int.lib.netex.get_status_of_import_collections")
    def test_retrieve_import_collection_status__is_successful_when_completed(self,
                                                                             mock_get_status_of_import_collections,
                                                                             mock_debug, _):

        mock_get_status_of_import_collections.return_value.json.return_value = {'createdTime': 1628161784007,
                                                                                'sessionId': 'fefb2920-89d2-40c4-8e4f'
                                                                                             '-5fb60ea8c8fe',
                                                                                'userId': 'NETEX_07_0805-12092953_u0', " \
         "'sessionType': 'IMPORT', 'status': 'COMPLETED_WITH_SUCCESS', 'objectType': 'COLLECTION', 'fileVersion': 'v1',
                                                                                'total': 4, 'processed': 3,
                                                                                'timeTaken': 4035,
                                                                                'failures': []}
        retrieve_import_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 2)
        self.assertEqual(self.profile.add_error_as_exception.call_count, 0)
        self.assertEqual(mock_get_status_of_import_collections.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.netex.handle_errors_in_retreive_import_collection_status")
    @patch("enmutils_int.lib.netex.log.logger.debug")
    @patch("enmutils_int.lib.netex.get_status_of_import_collections")
    def test_retrieve_import_collection_status__handles_exception_when_not_completed_after_attempts_completed(self,
                                                                                                              mock_get_status_of_import_collections,
                                                                                                              mock_debug,
                                                                                                              mock_handle_errors,
                                                                                                              *_):
        mock_get_status_of_import_collections.return_value.json.return_value = {'createdTime': 1628161784007,
                                                                                'sessionId': 'fefb2920-89d2-40c4-8e4f'
                                                                                             '-5fb60ea8c8fe',
                                                                                'userId': 'NETEX_07_0805-12092953_u0', " \
         "'sessionType': 'IMPORT', 'status': 'IN_PROGRESS', 'objectType': 'COLLECTION', 'fileVersion': 'v1', 'total': 4,
                                                                                'processed': 3, 'timeTaken': 4035,
                                                                                'failures': []}
        retrieve_import_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 2)
        self.assertEqual(mock_handle_errors.call_count, 1)
        self.assertEqual(mock_get_status_of_import_collections.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.netex.handle_errors_in_retreive_import_collection_status")
    @patch("enmutils_int.lib.netex.log.logger.debug")
    @patch("enmutils_int.lib.netex.get_status_of_import_collections")
    def test_retrieve_import_collection_status__handles_exception_when_no_content_in_get_status(self,
                                                                                                mock_get_status_of_import_collections,
                                                                                                mock_debug,
                                                                                                mock_handle_errors, _):
        mock_get_status_of_import_collections.return_value.json.return_value = {}
        retrieve_import_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 0)
        self.assertEqual(mock_handle_errors.call_count, 1)
        self.assertEqual(mock_get_status_of_import_collections.call_count, 1)

    @patch("time.sleep")
    @patch("enmutils_int.lib.netex.handle_errors_in_retreive_import_collection_status")
    @patch("enmutils_int.lib.netex.log.logger.debug")
    @patch("enmutils_int.lib.netex.get_status_of_import_collections")
    def test_retrieve_import_collection_status__handles_exception_when_error_in_get_status(self,
                                                                                           mock_get_status_of_import_collections,
                                                                                           mock_debug,
                                                                                           mock_handle_errors, _):
        mock_get_status_of_import_collections.side_effect = Exception
        retrieve_import_collection_status(self.profile, self.mock_user, "1", 1)
        self.assertEqual(mock_debug.call_count, 1)
        self.assertEqual(mock_handle_errors.call_count, 1)
        self.assertEqual(mock_get_status_of_import_collections.call_count, 1)

    @patch("enmutils_int.lib.netex.log.logger.debug")
    def test_handle_errors_in_retreive_import_collection_status__adds_exception_only(self, mock_debug):
        handle_errors_in_retreive_import_collection_status(0, 0, 1, Exception("test"), self.profile)
        self.assertEqual(self.profile.add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug.call_count, 0)

    @patch("enmutils_int.lib.netex.log.logger.debug")
    def test_handle_errors_in_retreive_import_collection_status__adds_exception_and_log_when_format_error(self,
                                                                                                          mock_debug):
        handle_errors_in_retreive_import_collection_status(1, 0, 1, Exception("test"), self.profile)
        self.assertEqual(self.profile.add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug.call_count, 1)

    @patch("enmutils_int.lib.netex.log.logger.debug")
    def test_handle_errors_in_retreive_import_collection_status__adds_exception_and_log_when_rest_error(self,
                                                                                                        mock_debug):
        handle_errors_in_retreive_import_collection_status(0, 1, 1, Exception("test"), self.profile)
        self.assertEqual(self.profile.add_error_as_exception.call_count, 1)
        self.assertEqual(mock_debug.call_count, 1)

    @patch("os.path.join")
    @patch("enmutils_int.lib.netex.filesystem.write_data_to_file")
    def test_create_export_dir_and_file__is_successful(self, mock_write_data_to_file, mock_path_join):
        create_export_dir_and_file("test_data", "test_file_name")
        self.assertEqual(mock_write_data_to_file.call_count, 1)
        self.assertEqual(mock_path_join.call_count, 1)


class NetexFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="netex_unit")
        self.large_collection = Mock()
        self.search = Mock()
        self.small_collection = Mock()
        self.profile = Mock()
        self.flow = NetexFlow(self.profile, self.user, "unit_query",
                              large_collection=self.large_collection,
                              small_collection=self.small_collection,
                              saved_search=self.search)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.netex.Search.delete', return_value=None)
    @patch('enmutils_int.lib.netex.Search.execute', side_effect=HTTPError("Exception"))
    @patch('enmutils_int.lib.netex.Search._get_saved_searches')
    def test_search_and_save__adds_exception_to_profile(self, mock_get_saved_searches, *_):
        profile = self.profile
        response = Mock()
        response.content = ["LTE01"]
        mock_get_saved_searches.return_value = response
        search_and_save(profile, Mock(), "LTE01", "unit_search", nodes=[Mock()], delete_existing=True)
        self.assertTrue(self.profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.netex.Search.save', return_value=None)
    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.Search._get_saved_searches')
    def test_search_and_save__is_successful(self, *_):
        profile = self.profile
        profile.nodes_list = []
        self.assertEqual(tuple, type(search_and_save(profile, Mock(), "LTE01", "unit_search", None)))

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.Collection')
    @patch('enmutils_int.lib.profile.Profile')
    def test_search_and_create_collection__adds_exception_to_profile_when_http_error(self, mock_profile,
                                                                                     mock_collection, *_):
        mock_collection.return_value.create.side_effect = HTTPError("Exception")
        search_and_create_collection(mock_profile, Mock(), "LTE01", "unit_collection", nodes=[])
        self.assertIsInstance(mock_profile.add_error_as_exception.call_args[0][0], EnmApplicationError)

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.Collection')
    def test_search_and_create_collection__is_successful_when_delete_existing_is_true(self, mock_collection,
                                                                                      mock_search_collections):
        test_collection_name = "unit_collection"
        mock_collection.return_value.name = test_collection_name
        mock_search_collections.return_value.json.return_value = [{"name": test_collection_name, "id": "1"}]
        profile = Mock()
        profile.nodes_list = []
        create_collection_response = search_and_create_collection(profile, Mock(), "LTE01", test_collection_name,
                                                                  nodes=[Mock()], delete_existing=True)
        self.assertIsInstance(create_collection_response, tuple)
        self.assertIsNotNone(create_collection_response[1])
        self.assertTrue(mock_collection.return_value.delete.called)
        self.assertEqual(profile.teardown_list.append.call_count, 1)

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.Collection')
    def test_search_and_create_collection__is_successful_when_delete_existing_is_false(self, mock_collection,
                                                                                       mock_search_collections):
        test_collection_name = "unit_collection"
        mock_collection.return_value.name = test_collection_name
        mock_search_collections.return_value.json.return_value = [{"name": test_collection_name, "id": "1"}]
        profile = Mock()
        profile.nodes_list = []
        create_collection_response = search_and_create_collection(profile, Mock(), "LTE01", test_collection_name,
                                                                  nodes=[Mock()], delete_existing=False)
        self.assertIsInstance(create_collection_response, tuple)
        self.assertIsNotNone(create_collection_response[1])
        self.assertFalse(mock_collection.return_value.delete.called)
        self.assertEqual(profile.teardown_list.append.call_count, 1)

    @patch('enmutils_int.lib.netex.get_all_collections')
    @patch('enmutils_int.lib.netex.Collection')
    def test_search_and_create_collection__is_successful_when_teardown_is_false(self, mock_collection, _):
        profile = self.profile
        profile.nodes_list = []
        create_collection_response = search_and_create_collection(profile, Mock(), "LTE01", "unit_collection",
                                                                  nodes=[Mock()], teardown=False)
        self.assertIsInstance(create_collection_response, tuple)
        self.assertIsNone(create_collection_response[1])
        self.assertEqual(profile.teardown_list.append.call_count, 0)

    @patch('enmutils_int.lib.netex.time.sleep', return_value=0)
    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    def test_navigate_netex_app_help__is_successful(self, mock_sleep, *_):
        self.flow._navigate_netex_app_help()
        self.assertEqual(mock_sleep.call_count, len(self.flow.NETEX_APP_HELP_URLS))

    @patch('enmutils_int.lib.netex.time.sleep')
    @patch('enmutils_int.lib.netex.log.logger.debug')
    def test_sleep__is_called(self, mock_debug, mock_sleep, *_):
        self.flow._sleep(0)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.netex.Search.execute', side_effect=HTTPError("Exception"))
    def test_execute_flow__adds_exception(self, *_):
        self.flow.execute_flow()
        self.assertTrue(self.profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    def test_execute_flow__is_successful(self, mock_sleep, *_):
        self.flow.execute_flow()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    def test_execute_flow__is_successful_when_execute_query_is_false(self, mock_sleep, *_):
        flow = NetexFlow(self.profile, self.user, "{node_id}")
        flow.execute_query = False
        flow.execute_flow()
        self.assertFalse(mock_sleep.called)

    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    def test_collection_query_flow__is_successful_for_query_with_large_collection_name(self, mock_sleep, *_):
        self.large_collection.id = "1.2.3.4"
        flow = NetexFlow(self.profile, self.user, "{large_collection_name}",
                         large_collection=self.large_collection)
        flow.collection_query_flow(collection=self.large_collection)
        self.assertTrue(mock_sleep.called)

    def test_collection_query_flow__adds_exception_for_query_with_large_collection_name_no_id(self, *_):
        self.large_collection.id = None
        flow = NetexFlow(Mock(), self.user, "{large_collection_name}",
                         large_collection=self.large_collection)
        flow.collection_query_flow(collection=self.large_collection)
        self.assertTrue(flow.profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.NetexFlow.collection_query_flow')
    def test_execute_flow__is_successful_for_query_with_small_collection_name(self, mock_collection_query_flow, *_):
        self.small_collection.id = "1"
        flow = NetexFlow(Mock(), self.user, "{small_collection_name}",
                         small_collection=self.small_collection)
        flow.execute_flow()
        self.assertTrue(mock_collection_query_flow.called)

    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.NetexFlow.collection_query_flow')
    def test_execute_flow__is_successful_for_query_with_large_collection_name(self, mock_collection_query_flow, *_):
        self.large_collection.id = "1"
        flow = NetexFlow(Mock(), self.user, "{large_collection_name}",
                         large_collection=self.large_collection)
        flow.execute_flow()
        self.assertTrue(mock_collection_query_flow.called)

    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.NetexFlow.search_query_flow')
    def test_execute_flow__is_successful_for_query_with_saved_search_name(self, mock_search_query_flow, *_):
        flow = NetexFlow(Mock(), self.user, "{saved_search_name}",
                         saved_search=self.search)
        flow.execute_flow()
        self.assertTrue(mock_search_query_flow.called)

    @patch('enmutils_int.lib.netex.Search.execute', return_value=None)
    @patch('enmutils_int.lib.netex.NetexFlow.query_on_partial_node_name')
    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    def test_execute_flow__is_successful_for_query_with_partial_node(self, mock_sleep, mock_query_on_partial_node_name,
                                                                     *_):
        flow = NetexFlow(Mock(), self.user, "{partial_node_regex}")
        flow.execute_flow()
        self.assertTrue(mock_query_on_partial_node_name.called)
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.netex.NetexFlow._sleep')
    def test_search_query_flow__is_successful_for_query_with_search_name(self, mock_sleep, *_):
        self.search.id = "1.2.3.4"
        flow = NetexFlow(self.profile, self.user, "{saved_search_name}",
                         saved_search=self.search)
        flow.search_query_flow(saved_search=self.search)
        self.assertTrue(mock_sleep.called)

    def test_search_query_flow__adds_exception__for_query_with_search_name_no_id(self, *_):
        self.search.id = None
        flow = NetexFlow(self.profile, self.user, "{saved_search_name}",
                         saved_search=self.search,
                         large_collection=self.large_collection)
        flow.search_query_flow(saved_search=self.search)
        self.assertTrue(self.profile.add_error_as_exception.called)

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name__is_successful_when_ieatnetsimv_present(self, mock_get_pos_by_poids,
                                                                                mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": [{"id": 1}]}
        mock_choice.return_value.__getitem__.return_value = 1
        mock_get_pos_by_poids.return_value.json.return_value = [{"moName": "ieatnetsimv010-07_RNC11RBS01"}]
        self.flow.query_on_partial_node_name()
        self.assertEqual(self.flow.query, "ieatnetsimv010-07_RNC11*")

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name__is_successful_when_core_present(self, mock_get_pos_by_poids, mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": [{"id": 1}]}
        mock_choice.return_value.__getitem__.return_value = 1
        mock_get_pos_by_poids.return_value.json.return_value = [{"moName": "CORE88MLTN6-0-1-01"}]
        self.flow.query_on_partial_node_name()
        self.assertEqual(self.flow.query, "CORE88*")

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name__is_successful_when_nr_present(self, mock_get_pos_by_poids, mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": [{"id": 1}]}
        mock_choice.return_value.__getitem__.return_value = 1
        mock_get_pos_by_poids.return_value.json.return_value = [{"moName": "NR01gNodeBRadio00001"}]
        self.flow.query_on_partial_node_name()
        self.assertEqual(self.flow.query, "NR01*")

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name__is_successful_for_others(self, mock_get_pos_by_poids, mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": [{"id": 1}]}
        mock_choice.return_value.__getitem__.return_value = 1
        mock_get_pos_by_poids.return_value.json.return_value = [{"moName": "LTE02dg2ERBS00001"}]
        self.flow.query_on_partial_node_name()
        self.assertEqual(self.flow.query, "LTE02*")

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name__raises_environ_warning_when_there_are_no_objects_in_collection(self,
                                                                                                        mock_get_pos_by_poids,
                                                                                                        mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": []}
        with self.assertRaises(EnvironWarning):
            self.flow.query_on_partial_node_name()

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name__raises_enm_error_when_get_collection_is_invalid(self, mock_get_pos_by_poids,
                                                                                         mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        mock_get_pos_by_poids.status_code = 400
        self.flow.small_collection.get_collection_by_id.return_value.text = None
        with self.assertRaises(EnmApplicationError):
            self.flow.query_on_partial_node_name()

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name____raises_enm_error_when_get_pos_by_poids_doesnt_have_text(self,
                                                                                                   mock_get_pos_by_poids,
                                                                                                   mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        mock_get_pos_by_poids.status_code = 401
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": [{"id": 1}]}
        mock_choice.return_value.__getitem__.return_value = 1
        mock_get_pos_by_poids.return_value.text = None
        with self.assertRaises(EnmApplicationError):
            self.flow.query_on_partial_node_name()

    @patch("enmutils_int.lib.netex.random.choice")
    @patch('enmutils_int.lib.netex.get_pos_by_poids')
    def test_query_on_partial_node_name____raises_enm_error_when_get_pos_by_poids_doesnt_have_mo_name(self,
                                                                                                      mock_get_pos_by_poids,
                                                                                                      mock_choice):
        self.flow.query = "{partial_node_regex}*"
        self.flow.small_collection = MagicMock()
        self.flow.small_collection.get_collection_by_id.return_value.json.return_value = {"contents": [{"id": 1}]}
        mock_choice.return_value.__getitem__.return_value = 1
        mock_get_pos_by_poids.return_value.json.return_value = [{"SomeName": "LTE02dg2ERBS00001"}]
        with self.assertRaises(EnmApplicationError):
            self.flow.query_on_partial_node_name()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
