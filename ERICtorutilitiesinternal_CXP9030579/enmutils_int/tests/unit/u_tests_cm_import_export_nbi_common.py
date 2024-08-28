#!/usr/bin/env python
import unittest2
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib import cm_import_export_nbi_common
from testslib import unit_test_utils


class CmImportExportNbiCommonUnitTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.cm_import_export_nbi_common.raise_for_status')
    def test_get_download_job_details_by_id_is_successful(self, *_):
        json_response_get_undo_success = {
            "id": 316,
            "status": "EXECUTED",
            "configuration": "Live"
        }
        response = Mock()
        response.json.return_value = json_response_get_undo_success
        self.user.get.return_value = response
        cm_import_export_nbi_common.get_download_job_details_by_id(self.user, job_id=316, end_point="location")
        self.assertTrue(self.user.get.called)

    @patch('enmutils_int.lib.cm_import_export_nbi_common.raise_for_status', side_effect=HTTPError)
    def test_get_download_job_details_by_id_raises_http_error(self, *_):
        self.user.get.return_value = HTTPError
        self.assertRaises(HTTPError, cm_import_export_nbi_common.get_download_job_details_by_id, self.user, 316,
                          end_point="location")

    @patch('enmutils_int.lib.cm_import_export_nbi_common.raise_for_status')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.write_to_file_location')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.get_download_job_details_by_id')
    def test_get_download_file_is_successful(self, mock_get_download_details, mock_write_to_file_location, *_):
        json_response_get_job_details_success = {
            "id": 177,
            "status": "COMPLETED",
            "fileUri": "/configuration/PZcVUIcLCYUEdfGZUWTRBPacTTVIHDAundo_2017-12-18T11-20-00_177.txt"
        }
        mock_get_download_details.return_value = json_response_get_job_details_success
        cm_import_export_nbi_common.get_download_file(self.user, job_id=177, operation="undo", end_point="location",
                                                      file_path="/configuration/")
        self.assertTrue(mock_get_download_details.called)
        self.assertTrue(mock_write_to_file_location.called)
        self.user.get.assert_called_with('/configuration/PZcVUIcLCYUEdfGZUWTRBPacTTVIHDAundo_2017-12-18T11-20-00_177.'
                                         'txt', stream=True)

    @patch('enmutils_int.lib.cm_import_export_nbi_common.raise_for_status', side_effect=HTTPError)
    @patch('enmutils_int.lib.cm_import_export_nbi_common.get_download_job_details_by_id')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.write_to_file_location')
    def test_get_download_file_raises_http_error(self, mock_write_to_file_location, *_):
        self.user.get.return_value = HTTPError
        self.assertRaises(HTTPError, cm_import_export_nbi_common.get_download_file, self.user, 117,
                          end_point="location", file_path="/con/")
        self.assertFalse(mock_write_to_file_location.called)

    @patch('enmutils_int.lib.cm_import_export_nbi_common.get_download_job_details_by_id')
    def test_get_download_file__raises_enm_application_error(self, mock_get_details):
        mock_get_details.return_value = {"fileUri": None}
        self.assertRaises(EnmApplicationError, cm_import_export_nbi_common.get_download_file, self.user, 117,
                          end_point="location", file_path="/con/")

    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.touch_file')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.log.logger.debug')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.write_data_to_file')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.create_dir')
    def test_write_to_file_location_is_successful(self, mock_create_dir, mock_write_data, mock_log, mock_touch_file,
                                                  *_):
        undo_file_uri = '/bulk/export/PZcVUIcLCYUEdfGZUWTRBPacTTVIHDAundo_2017-12-18T11-20-00_177.txt'
        file_response = Mock()
        cm_import_export_nbi_common.write_to_file_location(undo_file_uri, file_response, file_path="location",
                                                           operation="download")
        self.assertTrue(mock_create_dir.called)
        self.assertTrue(mock_write_data.called)
        self.assertEqual(mock_log.call_count, 2)
        self.assertTrue(mock_touch_file.called)

    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.touch_file')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.log.logger.debug')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.create_dir')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.write_data_to_file')
    def test_write_to_file_location__writes_to_dev_null(self, mock_write_data, *_):
        undo_file_uri = '/bulk/export/PZcVUIcLCYUEdfGZUWTRBPacTTVIHDAundo_2017-12-18T11-20-00_177.txt'
        file_response = Mock()
        cm_import_export_nbi_common.write_to_file_location(undo_file_uri, file_response, file_path="location",
                                                           operation="download", dev_null=True)
        mock_write_data.assert_called_with(output_file='/dev/null', data=file_response.content)

    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.does_file_exist', return_value=False)
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.touch_file')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.create_dir')
    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.write_data_to_file', side_effect=Exception("Error"))
    @patch('enmutils_int.lib.cm_import_export_nbi_common.log.logger.debug')
    def test_write_to_file_location__write_to_dev_null_logs_failure(self, mock_debug, *_):
        undo_file_uri = '/bulk/export/PZcVUIcLCYUEdfGZUWTRBPacTTVIHDAundo_2017-12-18T11-20-00_177.txt'
        file_response = Mock()
        cm_import_export_nbi_common.write_to_file_location(undo_file_uri, file_response, file_path="location",
                                                           operation="download", dev_null=True)
        mock_debug.assert_called_with('Error writing download file to location: /dev/null. Error encountered:: Error.')

    @patch('enmutils_int.lib.cm_import_export_nbi_common.filesystem.create_dir', side_effect=Exception)
    def test_write_to_file_location_raises_cm_import_error(self, *_):
        file_uri = '/configuration/PZcVUIcLCYUEdfGZUWTRBPacTTVIHDAundo_2019-12-18T11-20-00_177.txt'
        file_response = Mock()
        self.assertRaises(EnmApplicationError, cm_import_export_nbi_common.write_to_file_location, file_uri,
                          file_response, file_path="location", operation="undo")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
