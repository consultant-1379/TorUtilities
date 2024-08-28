#!/usr/bin/env python
import json
import unittest2
from requests.exceptions import HTTPError

from mock import patch, Mock

from enmutils_int.lib.parameter_management import (temporary_query_for_mo_class_mapping,
                                                   update_attributes,
                                                   get_parameter_set,
                                                   get_parameter_set_count,
                                                   create_parameter_set,
                                                   delete_parameter_set,
                                                   perform_netex_search,
                                                   get_fdns_from_poids,
                                                   TEST_DATA)
from testslib import unit_test_utils


class ParameterManagementUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.mock_user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_temporary_query_for_mo_class_mapping_is_successful(self):
        expected_json = {
            "moDetails": [{"moTypes": {"ENodeBFunction": [{"poId": "281475024838824", "nodeName": "LTE01"}]}}]}
        self.mock_user.get.return_value.json.return_value = expected_json
        self.assertEqual(temporary_query_for_mo_class_mapping(self.mock_user, "query"), expected_json)

    @patch("enmutils_int.lib.parameter_management.json.dumps")
    @patch("enmutils_int.lib.parameter_management.log.logger.debug")
    def test_update_attributes_is_successful(self, *_):
        po_data = {"attributes": [{"datatype": "INTEGER", "value": 148, "key": "combCellSectorSelectThreshRx"},
                                  {"datatype": "INTEGER", "value": 1709, "key": "combCellSectorSelectThreshTx"}],
                   "poId": "281475024838824",
                   "fdn": "SubNetwork=ERBS-SUBNW-1,MeContext=netsim_LTE103ERBS00003,ManagedElement=1,ENodeBFunction=1"}
        response = self.mock_user.put.return_value
        update_attributes(self.mock_user, po_data, po_data["attributes"])
        self.assertTrue(response.raise_for_status.called)

    def test_get_parameter_set(self):
        expected_response_text = '{"errorCode":0,"statusMessage":"OK","parameterSets":[{"id":"152786000","name":"pmset2","readOnly":false,"description":"testing on vapp","type":"USER_DEFINED","parameterDetails":null,"lastUpdated":1524228011266,"userId":"parmgt_02_0420-13385096_u0"}],"resultSize":1}'
        expected_response_dict = json.loads(expected_response_text)
        self.mock_user.get.return_value.text = expected_response_text
        self.assertEqual(get_parameter_set(self.mock_user), expected_response_dict)

    def test_get_parameter_set_count(self):
        expected_response_text = '{"errorCode":0,"statusMessage":"OK","parameterSets":[{"id":"152786000","name":"pmset2","readOnly":false,"description":"testing on vapp","type":"USER_DEFINED","parameterDetails":null,"lastUpdated":1524228011266,"userId":"parmgt_02_0420-13385096_u0"}],"resultSize":1}'
        expected_response_dict = json.loads(expected_response_text)
        self.mock_user.get.return_value.text = expected_response_text
        self.assertEqual(get_parameter_set_count(self.mock_user), expected_response_dict["resultSize"])

    def test_create_parameter_set(self):
        create_parameter_set(self.mock_user, data=TEST_DATA)
        self.assertTrue(self.mock_user.post.return_value.raise_for_status.called)

    def test_delete_parameter_set(self):
        delete_parameter_set(self.mock_user, parameter_set_ids=['1'])
        self.assertTrue(self.mock_user.delete_request.return_value.raise_for_status.called)

    @patch("enmutils_int.lib.parameter_management.chunks")
    @patch("enmutils_int.lib.parameter_management.get_pos_by_poids")
    def test_get_fdns_from_poids_success(self, mock_get_pos, mock_chunks):
        search = {"objects": [{"id": 7584573434}]}
        mock_user = Mock()
        mock_chunks.return_value = [1, 2, 3]
        get_fdns_from_poids(mock_user, search, Mock(), Mock())

        self.assertTrue(mock_chunks.called)
        self.assertTrue(mock_get_pos.called)

    @patch("time.sleep")
    @patch("enmutils_int.lib.parameter_management.chunks")
    @patch("enmutils_int.lib.parameter_management.get_pos_by_poids")
    def test_get_fdns_from_poids_retries_and_throws_http_error(self, mock_get_pos, mock_chunks, *_):
        search = {"objects": [{"id": 7584573434}]}
        mock_user = Mock()
        mock_get_pos.side_effect = [HTTPError(), HTTPError(), HTTPError()]
        mock_chunks.return_value = [1, 2, 3]

        self.assertRaises(HTTPError, get_fdns_from_poids, mock_user, search, Mock(), Mock())

    @patch("enmutils_int.lib.parameter_management.Search")
    def test_peform_netex_search(self, mock_search):
        perform_netex_search(Mock(), Mock())

        self.assertTrue(mock_search.called)

    @patch("time.sleep")
    @patch("enmutils_int.lib.parameter_management.Search")
    def test_peform_netex_search_retries_and_raises_http_error(self, mock_search, *_):
        mock_search_object = Mock()
        mock_search_object.execute.side_effect = [HTTPError(), HTTPError(), HTTPError()]
        mock_search.return_value = mock_search_object

        self.assertRaises(HTTPError, perform_netex_search, Mock, Mock)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
