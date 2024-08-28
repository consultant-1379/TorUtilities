#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, TimeOutError, EnmApplicationError
from enmutils_int.lib.enm_export import (CmExport, create_and_validate_cm_export_over_nbi,
                                         create_and_validate_cm_export,
                                         toggle_pib_historicalcmexport, ShmExport)
from enmutils_int.lib.workload.cmexport_02 import CMEXPORT_02
from enmutils_int.lib.workload.cmexport_03 import CMEXPORT_03
from enmutils_int.lib.workload.cmexport_08 import CMEXPORT_08
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase
from testslib import unit_test_utils


class ExportUnitTests(ParameterizedTestCase):

    def setUp(self):

        self.user = Mock(username="TestUser", password="T3stP4ssw0rd")
        unit_test_utils.setup()
        node = Mock()
        node.node_id = 'netsim_123'
        nodes = [node]
        self.job = CmExport(user=self.user, name='test', nodes=nodes, verify_timeout=0.1)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.enm_export.CmExport.create_over_nbi')
    def test__create_with_nbi_is_successful(self, mock_create_over_nbi, *_):
        self.job.interface = 'NBI'
        self.job._create()
        self.assertTrue(mock_create_over_nbi.called)

    @patch('enmutils_int.lib.enm_export.CmExport.create')
    def test__create_is_successful(self, mock_create):
        self.job._create()
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.enm_export.CmExport.create', side_effect=[Exception])
    def test__create_raises_exception(self, _):
        with self.assertRaises(Exception):
            self.job._create()

    @patch('enmutils_int.lib.enm_export.CmExport.validate_over_nbi')
    def test__validate_with_nbi_is_successful(self, mock_validate_over_nbi):
        self.job.interface = 'NBI'
        self.job._validate()
        self.assertTrue(mock_validate_over_nbi.called)

    @patch('enmutils_int.lib.enm_export.CmExport.validate')
    def test__validate_is_successful(self, mock_validate):
        self.job._validate()
        self.assertTrue(mock_validate.called)

    @patch('enmutils_int.lib.enm_export.CmExport.validate', side_effect=[Exception])
    def test__validate_raises_exception(self, _):
        with self.assertRaises(Exception):
            self.job._validate()

    @patch('enmutils_int.lib.enm_export.CmExport.construct_export_command')
    def test_001_create_sets_job_id_if_successful(self, _):
        response, self.job.user = Mock(), Mock()
        response.get_output.return_value = ['job setup successful with job ID 121']
        self.job.user.enm_execute.return_value = response
        self.job.create()
        self.assertEqual(self.job.job_id, '121')

    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_002_create_over_nbi__sets_job_id_if_successful(self, mock_set_scope):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = response
        self.job.create_over_nbi("CMEXPORT_03_0113-03455866_EXPORT")
        self.assertEqual(41, self.job.job_id)

    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_003_create_over_nbi__no_text_in_response_raises_enm_application_error(self, mock_set_scope):
        response = Mock(status_code=200, ok=True)
        response.text = None
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, self.job.create_over_nbi, "CMEXPORT_03_0112-03455866_EXPORT")

    @patch('enmutils_int.lib.enm_export.raise_for_status')
    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_004_create_over_nbi__no_response(self, mock_set_scope, _):
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = None
        self.assertRaises(EnmApplicationError, self.job.create_over_nbi, "CMEXPORT_03_0112-03455866_EXPORT")

    def test_005_get_export_job_by_id_is_successful(self):
        self.job.job_id = 1
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"status": 'COMPLETED'}
        self.user.get.return_value = response
        self.job.get_export_job_by_id()

    def test_006_get_export_job_by_id_raises_enm_application_error(self):
        self.assertRaises(EnmApplicationError, self.job.get_export_job_by_id)

    def test_007_get_export_job_by_id_raises_enm_application_error_if_not_int(self):
        self.job.job_id = "blah"
        self.assertRaises(EnmApplicationError, self.job.get_export_report_by_id)

    def test_009_get_export_report_by_id_is_successful(self):
        self.job.job_id = 1
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"status": 'COMPLETED'}
        self.user.get.return_value = response
        self.job.get_export_report_by_id()

    def test_011_get_export_report_by_id_raises_enm_application_error(self):
        self.assertRaises(EnmApplicationError, self.job.get_export_report_by_id)

    @patch('enmutils_int.lib.enm_export.raise_for_status')
    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_012_create_over_nbi__no_json(self, mock_set_scope, _):
        response = Mock(status_code=200, ok=True)
        response.json = None
        response.text = "Text"
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = response
        self.assertRaises(EnmApplicationError, self.job.create_over_nbi, "CMEXPORT_03_0112-03455866_EXPORT")

    def test_013_validate_over_nbi_raises_enm_application_error_if_not_int(self):
        self.job.job_id = "blah"
        self.assertRaises(EnmApplicationError, self.job.validate_over_nbi)

    def test_014_validate_over_nbi_raises_enm_application_error(self):
        self.job.job_id = 1
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"status": 'FAILED'}
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.job.validate_over_nbi)

    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_export.CmExport.get_export_job_by_id')
    def test_015_validate_over_nbi_success(self, mock_get_export, mock_debug):
        self.job.job_id = 1
        mock_get_export.return_value = {"status": 'COMPLETED'}
        self.job.validate_over_nbi()
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.enm_export.time.sleep')
    @patch('enmutils_int.lib.enm_export.CmExport.get_export_job_by_id')
    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    def test_016_no_node_matches_found_(self, mock_debug, mock_get_export, _):
        self.job.job_id = 1
        mock_get_export.side_effect = [
            {"status": 'STARTED'}, {"_links": {"self": {"href": "/bulk/export/reports/2677"}},
                                    "status": 'COMPLETED', "noMatchFoundResult": '["nodeName":"RNC03MSRBS-V2103"]'}]
        self.job.validate_over_nbi()
        self.assertTrue(mock_debug.called)

    @patch('enmutils_int.lib.enm_export.time.sleep')
    def test_017_validate_over_nbi_polls(self, mock_sleep):
        self.job.job_id = 1
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"status": 'STARTED'}
        self.user.get.return_value = response
        self.job.validate_over_nbi()
        self.assertTrue(mock_sleep.called)

    @patch('enmutils_int.lib.enm_export.CmExport.construct_export_command')
    @ParameterizedTestCase.parameterize(
        ('response_txt',),
        [
            (['job setup failed to create'],),
            (['Error 6008 : Invalid file name', 'Suggested Solution : Please specify a valid file name'],),
            (['Error 8009 : User defined filter content is invalid',
              'Suggested Solution : Specify a valid user defined filter content'],),
        ]
    )
    def test_018_create_raises_validation_error_if_unsuccessful(self, response_txt, _):
        response, self.job.user = Mock(), Mock()
        response.get_output.return_value = response_txt
        self.job.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.job.create)

    @patch('enmutils_int.lib.enm_export.time.sleep', return_value=0)
    @patch('enmutils_int.lib.enm_export.datetime')
    @patch('enmutils_int.lib.enm_export.CmExport.get_export_report_by_id')
    @patch('enmutils_int.lib.enm_export.CmExport.get_export_job_by_id')
    def test_019_validate_over_nbi__all_matches_found(self, mock_get_export, mock_get_report, mock_datetime, _):
        mock_datetime.datetime.now.return_value = 0
        mock_datetime.timedelta.return_value = 1
        self.job.job_id = 1
        mock_get_export.return_value = {"status": 'RUNNING'}
        mock_get_report.return_value = {"status": 'COMPLETED', "noMatchFoundResult": None}
        self.job.validate_over_nbi()
        self.assertEqual(1, mock_get_export.call_count)

    @patch('enmutils_int.lib.enm_export.time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.enm_export.CmExport.construct_export_command')
    def test_create__raises_runtime_error_if_unsuccessful(self, *_):
        response, self.job.user = Mock(), Mock()
        response.get_output.return_value = ['Error 8029 : License FAT1023443']
        self.job.user.enm_execute.return_value = response
        self.assertRaises(RuntimeError, self.job.create)

    def test_construct_export_command__using_ne_types(self):
        self.job.ne_types = ["ERBS", "RadioNode", "SGSN"]
        self.job.file_in = "some_file"
        self.job.interface = "NBI"
        self.job.config_name = "live"
        expected = "cmedit export --netype ERBS;RadioNode;SGSN --filetype 3GPP  --source live -jn test"
        self.assertEqual(self.job.construct_export_command(), expected)

    def test_construct_export_command__using_nodes_list(self):
        self.job.user_filter = "USER_FILTER"
        self.job.filter = "FILTER"
        self.job.file_compression = "gzip"
        expected = "cmedit export -n netsim_123 --filetype 3GPP  --filtername FILTER -jn test --filecompression gzip"
        self.assertEqual(self.job.construct_export_command(), expected)

    def test_construct_export_command__file_compression(self):
        self.job.user_filter = "USER_FILTER"
        self.job.filter = "FILTER"
        expected = "cmedit export -n netsim_123 --filetype 3GPP  --filtername FILTER -jn test"
        self.assertEqual(self.job.construct_export_command(), expected)

    def test_construct_export_command__batch_filter_true(self):
        self.job.user_filter = "USER_FILTER"
        self.job.batch_filter = "true"
        expected = "cmedit export -n netsim_123 --filetype 3GPP  -jn test --batchfilter true"
        self.assertEqual(self.job.construct_export_command(), expected)

    def test_construct_export_command__batch_filter_None(self):
        self.job.user_filter = "USER_FILTER"
        self.job.batch_filter = None
        expected = "cmedit export -n netsim_123 --filetype 3GPP  -jn test"
        self.assertEqual(self.job.construct_export_command(), expected)

    @patch('enmutils_int.lib.enm_export.time.sleep', side_effect=lambda _: None)
    @patch('enmscripting.common.element.ElementGroup')
    def test_get_job_status_table_raises_index_error(self, mock_element_group, *_):
        self.job.user = Mock()
        mock_element_group.groups.side_effect = [IndexError, IndexError, IndexError]
        mock_element_group.return_value = (((105, 'CMEXPORT_01_1010-14400065_EXPORT', 'COMPLETED',
                                             '2018-10-10T14:40:00', 216, 90, 0, 0, 248614,
                                             'CMEXPORT_01_1010-14374527_u0'),),)
        response = Mock()
        response.get_output.return_value = mock_element_group
        self.job.user.enm_execute.return_value = response
        with self.assertRaises(IndexError):
            self.job._get_job_status_table()

    @patch('enmutils_int.lib.enm_export.time.sleep', side_effect=lambda _: None)
    def test_get_job_status_table_raises_script_engine_response_validation_error(self, *_):
        self.job.user = Mock()
        self.job.user.enm_execute.side_effect = Exception
        with self.assertRaises(ScriptEngineResponseValidationError):
            self.job._get_job_status_table()

    def test_validate__raises_enm_application_error(self):
        self.job.job_id = None
        self.assertRaises(EnmApplicationError, self.job.validate)

    @patch('enmutils_int.lib.enm_export.time.sleep', return_value=0)
    @patch('enmutils_int.lib.enm_export.Export._get_job_status_table')
    @patch('enmutils_int.lib.enm_export.Export._extract_table_value')
    def test_validate__is_completed_successfully(self, mock_extract_table_value, mock_get_job_status_table, _):
        self.job.job_id = 1
        self.job.verify_timeout = 0.01
        self.job.polling_interval = 0.001
        self.job.user = Mock()
        mock_completed_status_table = (((105, 'CMEXPORT_01_1010-14400065_EXPORT', 'COMPLETED', '2018-10-10T14:40:00', 216, 90, 0, 0, 248614, 'CMEXPORT_01_1010-14374527_u0'),),)
        mock_started_status_table = (((105, 'CMEXPORT_01_1010-14400065_EXPORT', 'STARTED', '2018-10-10T14:40:00', 216, 90, 0, 0, 248614, 'CMEXPORT_01_1010-14374527_u0'),),)
        mock_get_job_status_table.side_effect = [mock_started_status_table, mock_completed_status_table]
        mock_extract_table_value.side_effect = ['STARTED', 'COMPLETED', 'CMEXPORT_TEST.xml']
        self.job.validate()

    @patch('enmutils_int.lib.enm_export.Export._extract_table_value')
    @patch('enmscripting.common.element.ElementGroup')
    def test_validate_is_completed_with_nodes_missing(self, mock_element_group, mock_extract_table_value):
        self.job.job_id = 1
        self.job.verify_timeout = 0.01
        self.job.user = Mock()
        mock_extract_table_value.return_value = 'COMPLETED - 2 nodes missing'
        mock_element_group.return_value = (((105, 'CMEXPORT_01_1010-14400065_EXPORT', 'COMPLETED', '2018-10-10T14:40:00', 216, 90, 0, 0, 248614, 'CMEXPORT_01_1010-14374527_u0'),),)
        response = Mock()
        response.get_output.return_value = mock_element_group
        self.job.user.enm_execute.return_value = response
        self.job.validate()

    @patch('enmutils_int.lib.enm_export.Export._extract_table_value')
    @patch('enmscripting.common.element.ElementGroup')
    def test_validate_raises_enm_application_error(self, mock_element_group, mock_extract_table_value):
        self.job.job_id = 1
        self.job.verify_timeout = 0.01
        self.job.user = Mock()
        mock_extract_table_value.return_value = 'FAILED'
        mock_element_group.return_value = (((105, 'CMEXPORT_01_1010-14400065_EXPORT', 'FAILED', '2018-10-10T14:40:00', 216, 90, 0, 0, 248614, 'CMEXPORT_01_1010-14374527_u0'),),)
        response = Mock()
        response.get_output.return_value = mock_element_group
        self.job.user.enm_execute.return_value = response
        with self.assertRaises(EnmApplicationError):
            self.job.validate()

    @patch('enmutils_int.lib.enm_export.Export._extract_table_value')
    @patch('enmscripting.common.element.ElementGroup')
    def test_validate_raises_timeout_error(self, mock_element_group, mock_extract_table_value):
        self.job.job_id = 1
        self.job.verify_timeout = 0
        self.job.user = Mock()
        mock_extract_table_value.return_value = 'FAILED'
        mock_element_group.return_value = (((105, 'CMEXPORT_01_1010-14400065_EXPORT', 'FAILED', '2018-10-10T14:40:00', 216, 90, 0, 0, 248614, 'CMEXPORT_01_1010-14374527_u0'),),)
        response = Mock()
        response.get_output.return_value = mock_element_group
        self.job.user.enm_execute.return_value = response
        with self.assertRaises(TimeOutError):
            self.job.validate()

    @patch('enmutils_int.lib.enm_export.Export._extract_table_value')
    @patch('enmscripting.common.element.ElementGroup')
    @patch('enmutils_int.lib.enm_export.Export._get_job_status_table')
    def test_validate_is_raises_enm_application_error_if_get_job_status_table_has_errors(self, mock_get_status_table, *_):
        self.job.job_id = 1
        self.job.verify_timeout = 0.1
        self.job.user = Mock()
        mock_get_status_table.side_effect = Exception
        with self.assertRaises(EnmApplicationError):
            self.job.validate()

    def test_extract_table_value__returns_element_group_value(self):
        element_group = Mock()
        element_group.value.return_value = "Some Value"
        job_status_table = Mock()
        job_status_table.find_by_label.return_value = [element_group]
        self.assertEqual(self.job._extract_table_value(job_status_table, "Ne Type"), "Some Value")

    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    def test_delete__success(self, mock_debug):
        response = Mock()
        response.get_output.return_value = ['Export job was successfully removed.']
        self.user.enm_execute.return_value = response
        self.job.job_id = "121"
        self.job.delete()
        mock_debug.assert_called_with("Script engine response for export delete command for test is Export job was "
                                      "successfully removed.")

    def test_delete__raises_enm_application_error(self):
        self.job.job_id = None
        self.assertRaises(EnmApplicationError, self.job.delete)

    def test_022_delete_raises_error_if_incorrect_response_received(self):
        response = Mock()
        response.get_output.return_value = ['job delete was not successful with job ID 121']
        self.user.enm_execute.return_value = response
        self.job.job_id = "121"
        self.assertRaises(ScriptEngineResponseValidationError, self.job.delete)

    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_023_create_over_nbi_sets_job_id_with_for_cnm_if_successful(self, mock_set_scope):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = response
        self.job.user_filter = ("ManagedElement.(managedElementType);Ip.(nodeIpAddress,nodeIpv6Address,"
                                "nodeIpv6InterfaceName);AddressIPv6.(address);AddressIPv4.(address);")
        self.job.create_over_nbi("CMEXPORT_19")
        self.assertEqual(41, self.job.job_id)

    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_023_create_over_nbi_sets_job_id_with_user_defined_filter_if_successful(self, mock_set_scope):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = response
        self.job.user_filter = ("ManagedElement.(managedElementType);Ip.(nodeIpAddress,nodeIpv6Address,"
                                "nodeIpv6InterfaceName);AddressIPv6.(address);AddressIPv4.(address);")
        self.job.create_over_nbi("CMEXPORT_03_0113-03455866_EXPORT")
        self.assertEqual(41, self.job.job_id)

    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_024_create_over_nbi_sets_job_id_with_filter_if_successful(self, mock_set_scope):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        mock_set_scope.return_value = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': ''}]
        self.user.post.return_value = response
        self.job.filter = "SON"
        self.job.create_over_nbi("CMEXPORT_03_0113-03455866_EXPORT")
        self.assertEqual(41, self.job.job_id)

    @patch('enmutils_int.lib.enm_export.CmExport.set_nbi_search_criteria')
    def test_025_create_over_nbi__does_not_add_node_scope_if_no_nodes_or_regex_supplied(self, mock_set_scope):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"id": 41}
        self.user.post.return_value = response
        self.job.nodes, self.job.node_regex = None, None
        self.job.filter = "SON"
        self.job.create_over_nbi("CMEXPORT_03_0113-03455866_EXPORT")
        self.assertEqual(41, self.job.job_id)
        self.assertEqual(0, mock_set_scope.call_count)

    def test_set_nbi_search_criteria__regex(self):
        self.job.node_regex = "*Pattern*;*Pattern1*;*Pattern2*"
        expected = [{'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': 'Pattern'},
                    {'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': 'Pattern1'},
                    {'matchCondition': 'CONTAINS', 'scopeType': 'NODE_NAME', 'value': 'Pattern2'}]
        result = self.job.set_nbi_search_criteria()
        self.assertListEqual(expected, result)

    def test_set_nbi_search_criteria__node_names(self):
        nodes = [Mock(node_id="Node"), Mock(node_id="Node1")]
        self.job.node_regex = None
        self.job.nodes = nodes
        expected = [{'matchCondition': 'EQUALS', 'scopeType': 'NODE_NAME', 'value': 'Node'},
                    {'matchCondition': 'EQUALS', 'scopeType': 'NODE_NAME', 'value': 'Node1'}]
        result = self.job.set_nbi_search_criteria()
        self.assertListEqual(expected, result)

    def test_set_nbi_search_criteria__ne_types(self):
        self.job.node_regex = None
        self.job.nodes = None
        self.job.ne_types = ["ERBS", "RadioNode"]
        expected = [{'matchCondition': 'NO_MATCH_REQUIRED', 'scopeType': 'UNSPECIFIED', 'neType': 'ERBS'},
                    {'matchCondition': 'NO_MATCH_REQUIRED', 'scopeType': 'UNSPECIFIED', 'neType': 'RadioNode'}]
        result = self.job.set_nbi_search_criteria()
        self.assertListEqual(expected, result)

    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_export.CmExport')
    def test_create_and_validate_cm_export_over_nbi_is_successful(self, mock_cmexport, mock_logger_debug):
        mock_cmexport.name = 'EXPORT_0'
        profile = CMEXPORT_08()
        create_and_validate_cm_export_over_nbi(mock_cmexport, profile)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_export.time.sleep')
    @patch('enmutils_int.lib.enm_export.CmExport')
    def test_create_and_validate_cm_export_over_nbi_raises_exception(self, mock_cmexport, mock_time_sleep, _):
        mock_cmexport.name = 'EXPORT_0'
        mock_cmexport.create_over_nbi.side_effect = Exception()
        profile = CMEXPORT_03()
        profile.add_error_as_exception = Mock()
        create_and_validate_cm_export_over_nbi(mock_cmexport, profile)
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_time_sleep.called)

    @patch('enmutils_int.lib.enm_export.time.sleep')
    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_export.CmExport')
    def test_create_and_validate_cm_export_is_successful(self, mock_cmexport, mock_logger_debug, _):
        profile = CMEXPORT_02()
        profile.add_error_as_exception = Mock()
        create_and_validate_cm_export(mock_cmexport, profile)
        self.assertTrue(mock_logger_debug.called)
        self.assertFalse(profile.add_error_as_exception.called)

    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_export.time.sleep')
    @patch('enmutils_int.lib.enm_export.CmExport')
    def test_create_and_validate_cm_export_raises_exception(self, mock_cmexport, mock_time_sleep, _):
        mock_cmexport.create.side_effect = Exception()
        profile = CMEXPORT_02()
        profile.add_error_as_exception = Mock()
        create_and_validate_cm_export(mock_cmexport, profile)
        self.assertTrue(profile.add_error_as_exception.called)
        self.assertTrue(mock_time_sleep.called)

    @patch('enmutils_int.lib.enm_export.shell.run_cmd_on_emp_or_ms')
    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.get_values_from_global_properties')
    def test_toggle_pib_historicalcmexport__is_successful(self, mock_get_values_from_global_properties,
                                                          mock_logger_debug, mock_run_cmd_on_emp_or_ms):
        response = Mock()
        response.rc = 0
        mock_get_values_from_global_properties.return_value = ['ip', 'ip']
        mock_run_cmd_on_emp_or_ms.return_value = response
        toggle_pib_historicalcmexport('true')
        mock_logger_debug.assert_called_with("ENIQ Historical CM Export is enabled. ")

    @patch('enmutils_int.lib.enm_export.shell.run_cmd_on_emp_or_ms')
    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_deployment.get_values_from_global_properties')
    def test_toggle_pib_historicalcmexport_raises_enm_application_error(self, mock_get_values_from_global_properties,
                                                                        mock_logger_debug, mock_run_cmd_on_emp_or_ms):
        response = Mock()
        response.rc = 1
        mock_get_values_from_global_properties.return_value = ['ip', 'ip']
        mock_run_cmd_on_emp_or_ms.return_value = response
        self.assertRaises(EnmApplicationError, toggle_pib_historicalcmexport, 'true')
        self.assertEqual(mock_logger_debug.call_count, 0)

    @patch('enmutils_int.lib.enm_export.shell.run_cmd_on_emp_or_ms')
    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    @patch('enmutils_int.lib.enm_export.enm_deployment.get_values_from_global_properties')
    def test_toggle_pib_historicalcmexport__is_successful_when_toggled_to_false(
            self, mock_get_values_from_global_properties, mock_logger_debug, mock_run_cmd_on_emp_or_ms):
        response = Mock()
        response.rc = 0
        mock_get_values_from_global_properties.return_value = ['ip', 'ip']
        mock_run_cmd_on_emp_or_ms.return_value = response
        toggle_pib_historicalcmexport('false')
        mock_logger_debug.assert_called_with("ENIQ Historical CM Export is disabled. ")

    def test_em_exmport_exists(self):
        response = Mock()
        response.json.return_value = {u"jobs": [{u'jobName': u'NotTheJobYou\'reLookingFor'}, {u'jobName': u'test'}]}
        self.user.get.return_value = response
        self.assertTrue(self.job.exists())
        response.json.return_value = {u"jobs": [{u'jobName': u'NotTheJobYou\'reLookingFor'}]}
        self.assertFalse(self.job.exists())
        response.json.return_value = None
        self.assertFalse(self.job.exists())

    @patch('enmutils_int.lib.enm_export.log.logger.debug')
    def test_em_exmport_exists_exception_is_logged(self, mock_debug):
        self.user.get.side_effect = Exception("Connection aborted")
        self.job.exists()
        mock_debug.assert_called_with("Failed to confirm job exists, response: Connection aborted")


class ShmExportUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.export = ShmExport(user=self.user, export_type="lic", name="1234", saved_search_name="query")

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_create__success(self):
        response = Mock()
        response.get_output.return_value = [u'', u'Export job 1234 started with job ID 151']
        self.user.enm_execute.return_value = response
        self.export.create()
        self.assertEqual(self.export.job_id, "151")

    def test_create__raises_script_engine_error(self):
        response = Mock()
        response.get_output.return_value = [u'', u'Error']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.export.create)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
