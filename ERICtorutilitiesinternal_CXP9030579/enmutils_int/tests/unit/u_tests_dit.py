#!/usr/bin/env python
import unittest2

import enmutils_int.lib.dit as dit
from mock import patch, Mock, call
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class DITUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.dit.commands.getstatusoutput', return_value=(0, "some output"))
    def test_send_request_to_dit__is_successful(self, mock_getstatusoutput):
        result = dit.send_request_to_dit("content_url")
        self.assertEqual(result, "some output")
        mock_getstatusoutput.assert_called_with("curl -s 'https://atvdit.athtem.eei.ericsson.se/api/content_url'")

    @patch('enmutils_int.lib.dit.commands.getstatusoutput', return_value=(1, "error"))
    @patch('enmutils_int.lib.dit.log.logger.debug')
    def test_send_request_to_dit__returns_none_if_error_encountered_running_curl_comand(self, mock_debug, _):
        result = dit.send_request_to_dit("content_url")
        self.assertEqual(result, None)
        self.assertTrue(call("Problem encountered while fetching data from DIT: 'error'") in mock_debug.mock_calls)

    @patch('enmutils_int.lib.dit.commands.getstatusoutput', return_value=(0, ""))
    @patch('enmutils_int.lib.dit.log.logger.debug')
    def test_send_request_to_dit__returns_none_if_no_data_returned_from_dit(self, mock_debug, _):
        result = dit.send_request_to_dit("content_url")
        self.assertEqual(result, None)
        self.assertTrue(call("No data returned from DIT") in mock_debug.mock_calls)

    @patch('enmutils_int.lib.dit.send_request_to_dit', return_value="some output")
    @patch('enmutils_int.lib.dit.parse_documents_data')
    def test_get_documents_info_from_dit__is_successful(self, mock_parse_documents_data, mock_send_request_to_dit):
        result = dit.get_documents_info_from_dit("ENM123")
        self.assertEqual(mock_parse_documents_data.return_value, result)
        mock_send_request_to_dit.assert_called_with(r"deployments/?q=name=ENM123&fields=documents")
        mock_parse_documents_data.assert_called_with("some output")

    @patch('enmutils_int.lib.dit.send_request_to_dit', return_value="")
    @patch('enmutils_int.lib.dit.parse_documents_data')
    def test_get_documents_info_from_dit__handles_empty_data(self, mock_parse_documents_data, mock_send_request_to_dit):
        dit.get_documents_info_from_dit("ENM123")
        mock_send_request_to_dit.assert_called_with(r"deployments/?q=name=ENM123&fields=documents")
        self.assertFalse(mock_parse_documents_data.called)

    @patch('enmutils_int.lib.dit.json.loads')
    def test_parse_documents_data(self, mock_loads):
        json_loads_output = [
            {
                "documents": [
                    {"document_id": "id1", "schema_category": "other", "schema_name": "name1"},
                    {"document_id": "id2", "schema_category": "other", "schema_name": "name2"},
                    {"document_id": "id3", "schema_category": "other", "schema_name": "name3"},
                ]
            }
        ]
        mock_loads.return_value = json_loads_output
        documents_info_dict = {"name1": "id1", "name2": "id2", "name3": "id3"}
        self.assertEqual(documents_info_dict, dit.parse_documents_data(Mock()))

    @patch('enmutils_int.lib.dit.json.loads', side_effect=Exception("some error"))
    @patch('enmutils_int.lib.dit.log.logger.debug')
    def test_parse_documents_data__handles_format_error(self, mock_debug, _):
        dit.parse_documents_data("some output")
        self.assertTrue(call("Data received from DIT in unexpected format:- Data: 'some output', Error: 'some error'")
                        in mock_debug.mock_calls)

    @patch('enmutils_int.lib.dit.send_request_to_dit', return_value="some output")
    @patch('enmutils_int.lib.dit.extract_document_content')
    def test_get_document_content_from_dit__successful(self, mock_extract_document_content, mock_send_request_to_dit):
        result = dit.get_document_content_from_dit("some_id")
        self.assertEqual(mock_extract_document_content.return_value, result)
        mock_send_request_to_dit.assert_called_with(r"documents/some_id?fields=content")
        mock_extract_document_content.assert_called_with("some output")

    @patch('enmutils_int.lib.dit.send_request_to_dit', return_value="")
    @patch('enmutils_int.lib.dit.extract_document_content')
    def test_get_document_content_from_dit__handles_empty_data_from_dit(
            self, mock_extract_document_content, mock_send_request_to_dit):
        result = dit.get_document_content_from_dit("some_id")
        self.assertEqual(None, result)
        mock_send_request_to_dit.assert_called_with(r"documents/some_id?fields=content")
        self.assertFalse(mock_extract_document_content.called)

    @patch('enmutils_int.lib.dit.json.loads')
    def test_extract_document_content__successful(self, mock_loads):
        some_content = {"key1": "value1"}
        mock_loads.return_value = {"content": some_content}
        self.assertEqual(some_content, dit.extract_document_content("some output"))

    @patch('enmutils_int.lib.dit.json.loads', side_effect=Exception("some error"))
    @patch('enmutils_int.lib.dit.log.logger.debug')
    def test_extract_document_content__handles_format_error(self, mock_debug, _):
        dit.extract_document_content("some output")
        self.assertTrue(call("Data received from DIT in unexpected format:- Data: 'some output', Error: 'some error'")
                        in mock_debug.mock_calls)

    @patch("enmutils_int.lib.dit.log.logger.info")
    def test_determine_deployment_type__returns_cenm_if_cENM_site_information_identifier_found(self, mock_info):
        self.assertEqual("cENM", dit.determine_deployment_type({"cENM_site_information": "12345"}))
        mock_info.assert_called_with("Deployment type detected: cENM ('cENM_site_information' document found on DIT)")

    @patch("enmutils_int.lib.dit.log.logger.info")
    def test_determine_deployment_type__returns_venm_if_cENM_site_information_identifier_not_found(self, mock_info):
        self.assertEqual("vENM", dit.determine_deployment_type({"something_else": "12345"}))
        mock_info.assert_called_with("Deployment type detected: vENM (no 'cENM_site_information' document found on DIT)")

    @patch("enmutils_int.lib.dit.extract_sed_id_from_sed_document", return_value="12345")
    @patch("enmutils_int.lib.dit.send_request_to_dit", return_value="some_output")
    def test_get_sed_id__successful(self, mock_send_request_to_dit, mock_extract_sed_id_from_sed_document):
        self.assertEqual("12345", dit.get_sed_id("some_deployment"))
        url = r"deployments/?q=name=some_deployment&fields=enm(sed_id)"
        mock_send_request_to_dit.assert_called_with(url)
        mock_extract_sed_id_from_sed_document.assert_called_with("some_output")

    @patch("enmutils_int.lib.dit.extract_sed_id_from_sed_document")
    @patch("enmutils_int.lib.dit.send_request_to_dit", return_value=None)
    def test_get_sed_id__returns_none_if_sed_doc_not_found(
            self, mock_send_request_to_dit, mock_extract_sed_id_from_sed_document):
        self.assertEqual(None, dit.get_sed_id("some_deployment"))
        url = r"deployments/?q=name=some_deployment&fields=enm(sed_id)"
        mock_send_request_to_dit.assert_called_with(url)
        self.assertFalse(mock_extract_sed_id_from_sed_document.called)

    @patch("enmutils_int.lib.dit.json.loads", return_value=[{"enm": {"sed_id": "12345"}}])
    def test_extract_sed_id_from_sed_document__successful(self, mock_loads):
        output = Mock()
        self.assertEqual("12345", dit.extract_sed_id_from_sed_document(output))
        mock_loads.assert_called_with(output)

    @patch("enmutils_int.lib.dit.json.loads", return_value=[{"enm": {"sed_id_value": "12345"}}])
    def test_extract_sed_id_from_sed_document__handles_unexpected_format(self, mock_loads):
        output = Mock()
        self.assertEqual(None, dit.extract_sed_id_from_sed_document(output))
        mock_loads.assert_called_with(output)

    @patch("enmutils_int.lib.dit.extract_parameter_value_from_sed_document", return_value="some_value")
    @patch("enmutils_int.lib.dit.send_request_to_dit", return_value="some_output")
    def test_get_parameter_value_from_sed_document__successful(
            self, mock_send_request_to_dit, mock_extract_parameter_value_from_sed):
        self.assertEqual("some_value", dit.get_parameter_value_from_sed_document("12345", "some_parameter"))
        url = r"documents/12345?fields=content(parameters(some_parameter))"
        mock_send_request_to_dit.assert_called_with(url)
        mock_extract_parameter_value_from_sed.assert_called_with("some_output", "some_parameter")

    @patch("enmutils_int.lib.dit.extract_parameter_value_from_sed_document")
    @patch("enmutils_int.lib.dit.send_request_to_dit", return_value=None)
    def test_get_parameter_value_from_sed_document__returns_none_if_unable_to_fetch_data(
            self, mock_send_request_to_dit, mock_extract_parameter_value_from_sed):
        self.assertEqual(None, dit.get_parameter_value_from_sed_document("12345", "some_parameter"))
        url = r"documents/12345?fields=content(parameters(some_parameter))"
        mock_send_request_to_dit.assert_called_with(url)
        self.assertFalse(mock_extract_parameter_value_from_sed.called)

    @patch("enmutils_int.lib.dit.json.loads", return_value={"content": {"parameters": {"some_parameter": "12345"}}})
    def test_extract_parameter_value_from_sed_document__successful(self, mock_loads):
        output = Mock()
        self.assertEqual("12345", dit.extract_parameter_value_from_sed_document(output, "some_parameter"))
        mock_loads.assert_called_with(output)

    @patch("enmutils_int.lib.dit.json.loads", return_value={"content": {"parameters_all": {"some_parameter": "12345"}}})
    def test_extract_parameter_value_from_sed_document__handles_unexpected_format(self, mock_loads):
        output = Mock()
        self.assertEqual(None, dit.extract_parameter_value_from_sed_document(output, "some_parameter"))
        mock_loads.assert_called_with(output)

    @patch("enmutils_int.lib.dit.get_document_content_from_dit", return_value={"global": {"namespace": "enm123"}})
    def test_get_deployment_namespace__successful(self, mock_get_document_content_from_dit):
        self.assertEqual("enm123",
                         dit.get_deployment_namespace("deployment_name", {"cENM_site_information": "12345"}))
        mock_get_document_content_from_dit.assert_called_with("12345")

    @patch("enmutils_int.lib.dit.log.logger.debug")
    @patch("enmutils_int.lib.dit.log.logger.warn")
    @patch("enmutils_int.lib.dit.get_document_content_from_dit", return_value={"global": {"namespace": ""}})
    def test_get_deployment_namespace__returns_none_if_namespace_not_set(self, mock_get_document_content_from_dit,
                                                                         mock_warn, _):
        self.assertIsNone(dit.get_deployment_namespace("deployment_name", {"cENM_site_information": "12345"}))
        self.assertTrue(mock_get_document_content_from_dit.called)
        mock_warn.assert_called_once_with("Unable to retrieve cENM_site_information document from DIT")

    @patch("enmutils_int.lib.dit.log.logger.debug")
    @patch("enmutils_int.lib.dit.log.logger.warn")
    @patch("enmutils_int.lib.dit.get_document_content_from_dit", return_value={"NAMESPACE": ""})
    def test_get_deployment_namespace__returns_none_if_no_doc_id_set(self, mock_get_document_content_from_dit,
                                                                     mock_warn, _):
        self.assertIsNone(dit.get_deployment_namespace("deployment_name", {"cENM_site_information": ""}))
        self.assertFalse(mock_get_document_content_from_dit.called)
        mock_warn.assert_called_once_with("The document 'cENM_site_information' was not found on"
                                          " DIT for deployment deployment_name")

    @patch("enmutils_int.lib.dit.determine_deployment_type", return_value="cENM")
    @patch("enmutils_int.lib.dit.get_documents_info_from_dit", return_value={"key1": "value1"})
    def test_get_dit_deployment_info__successful_if_variables_not_set(
            self, mock_get_documents_info_from_dit, mock_determine_deployment_type):
        dit.DEPLOYMENT_TYPE, dit.DIT_DOCUMENTS_INFO_DICT = None, None
        self.assertEqual(("cENM", {"key1": "value1"}), dit.get_dit_deployment_info("deployment_name"))
        mock_get_documents_info_from_dit.assert_called_with("deployment_name")
        mock_determine_deployment_type.assert_called_with({"key1": "value1"})

    @patch("enmutils_int.lib.dit.determine_deployment_type")
    @patch("enmutils_int.lib.dit.get_documents_info_from_dit")
    def test_get_dit_deployment_info__successful_if_variables_are_set(
            self, mock_get_documents_info_from_dit, mock_determine_deployment_type):
        dit.DEPLOYMENT_TYPE, dit.DIT_DOCUMENTS_INFO_DICT = "cENM", {"key1": "value1"}
        self.assertEqual(("cENM", {"key1": "value1"}), dit.get_dit_deployment_info("deployment_name"))
        self.assertFalse(mock_get_documents_info_from_dit.called)
        self.assertFalse(mock_determine_deployment_type.called)

    @patch("enmutils_int.lib.dit.determine_deployment_type")
    @patch("enmutils_int.lib.dit.get_documents_info_from_dit", return_value=None)
    def test_get_dit_deployment_info__unsuccessful_if_no_data_in_dit(
            self, mock_get_documents_info_from_dit, mock_determine_deployment_type):
        dit.DEPLOYMENT_TYPE, dit.DIT_DOCUMENTS_INFO_DICT = None, {}
        with self.assertRaises(Exception) as e:
            dit.get_dit_deployment_info("deployment_name")
        self.assertEqual(e.exception.message, "Unable to get documents info from DIT for this deployment")
        self.assertTrue(mock_get_documents_info_from_dit.called)
        self.assertFalse(mock_determine_deployment_type.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
