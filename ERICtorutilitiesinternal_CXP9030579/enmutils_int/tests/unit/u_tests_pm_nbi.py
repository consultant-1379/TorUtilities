#!/usr/bin/env python
import unittest2
from mock import MagicMock, patch, call, Mock

from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib import pm_nbi
from testslib import unit_test_utils


class PmNbiUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.fls_url = '/file/v1/files/'
        self.fls = pm_nbi.Fls(user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_pmic_rop_files_location__is_successful(self):
        files_data = []

        for count in range(10):
            files_data.append({"id": count, "fileCreationTimeInOss": "{}+sometime".format(count),
                               "nodeName": "node_name{}".format(count),
                               "fileLocation": "filename_blah{}".format(count)})
        response = Mock(status=200)
        response.ok = True
        response.json.return_value = {"files": files_data}
        self.fls.user.get.return_value = response
        files, file_id, _ = self.fls.get_pmic_rop_files_location("PM_44", "PM_STATISTICAL", file_id=1)
        self.assertEqual(len(files), 10)
        self.assertEqual(file_id, 9)

    def test_get_pmic_rop_files_location__fetches_files_again_if_more_than_10000_for_given_profile(self):
        files_data = []
        for count in range(1, 15901):
            files_data.append({"id": count, "fileCreationTimeInOss": "{}+sometime".format(count),
                               "nodeName": "node_name{}".format(count),
                               "fileLocation": "filename_blah{}".format(count)})
        response = Mock(status=200, ok=True)
        response.json.return_value = {"files": files_data[:10000]}
        second_response = Mock(status=200, ok=True)
        second_response.json.return_value = {"files": files_data[10000:]}
        self.fls.user.get.side_effect = [response, second_response]
        files, file_id, _ = self.fls.get_pmic_rop_files_location("PM_26", "PM_STATISTICAL", file_id=1)
        self.assertEqual(len(files), 15900)
        self.assertEqual(file_id, 15900)

    def test_get_pmic_rop_files_location__is_successful_even_if_second_request_to_get_files_returns_empty_list(self):
        files_data = []
        for count in range(1, 10001):
            files_data.append({"id": count, "fileCreationTimeInOss": "{}+sometime".format(count),
                               "nodeName": "node_name{}".format(count),
                               "fileLocation": "filename_blah{}".format(count)})
        response = Mock(status=200, ok=True)
        response.json.return_value = {"files": files_data}
        second_response = Mock(status=200, ok=True)
        second_response.json.return_value = {"files": []}
        self.fls.user.get.side_effect = [response, second_response]
        files, file_id, _ = self.fls.get_pmic_rop_files_location("PM_26", "PM_STATISTICAL", file_id=1)
        self.assertEqual(len(files), 10000)
        self.assertEqual(file_id, 10000)

    def test_get_pmic_rop_files_location__error_response(self):
        response = Mock(status=404, ok=False)
        response.json.return_value = {"files": []}
        self.user.get.return_value = response
        self.assertRaises(EnmApplicationError, self.fls.get_pmic_rop_files_location, "PM_44", "PM_STATISTICAL")

    def test_get_pmic_rop_files_location__no_max_id(self):
        response = Mock(status=200, ok=True)
        response.json.return_value = {"files": []}
        self.user.get.return_value = response
        files, file_id, _ = self.fls.get_pmic_rop_files_location("PM_26", "PM_STATISTICAL", file_id=0)
        self.assertEqual(len(files), 0)
        self.assertEqual(file_id, 0)

    def test_get_pmic_rop_files_location__ok_response_no_files_returned_from_fls(self):
        response = Mock(status=200, ok=True)
        response.json.return_value = {"files": []}
        self.user.get.side_effect = [response, response]
        self.assertEqual(([], 0, None), self.fls.get_pmic_rop_files_location("PM_44", "PM_STATISTICAL"))
        self.assertEqual(([], 0, None), self.fls.get_pmic_rop_files_location("PM_44", "PM_STATISTICAL"))

    def test_get_pmic_rop_files_location__one_file(self):
        response = Mock()
        response.json.return_value = {"files": [{"id": 2, "fileCreationTimeInOss": "time", "nodeName": "node_name1",
                                                 "fileLocation": "filename_blah1"}]}
        self.user.get.return_value = response
        files = self.fls.get_pmic_rop_files_location("PM_26", "PM_STATISTICAL", file_id=1)
        self.assertEqual(files, (["filename_blah1"], 2, "time"))

    def test_url_builder__is_successful(self):
        url = self.fls._url_builder("PM_STATISTICAL", node_type="ERBS", file_type="xml", file_id=0, start_rop_time="2017-01-01T12:00:00")
        self.assertEqual(url, ("/file/v1/files/?filter=dataType==PM_STATISTICAL;nodeType==ERBS;fileType==xml;"
                               "startRopTimeInOss==2017-01-01T12:00:00&select=id,nodeName,fileLocation,nodeType,fileCreationTimeInOss,dataType"))

    def test_url_builder__if_url_size_is_short(self):
        url = self.fls._url_builder("PM_STATISTICAL")
        self.assertEqual(url, "/file/v1/files/?filter=dataType==PM_STATISTICAL&select=id,nodeName,fileLocation,nodeType,fileCreationTimeInOss,dataType")

    @patch('__builtin__.open')
    def test_create_sftp_batch_files__is_successful(self, mock_open):
        mock_open.return_value = MagicMock(spec=file)
        self.fls.create_sftp_batch_files(["file_path1", "file_path2"], "/dev/null", "/tmp/pm_nbi_batch_{:02d}",
                                         num_of_sftp_batch_files=2)
        self.assertTrue(mock_open.called)
        file_handle = mock_open.return_value.__enter__.return_value
        file_handle.write.assert_has_calls([call('-get file_path2 /dev/null\n'), call('-get file_path1 /dev/null\n')],
                                           any_order=True)

    @patch('enmutils_int.lib.pm_nbi.random.shuffle')
    @patch('__builtin__.open')
    def test_create_sftp_batch_files__shuffle_not_called(self, mock_open, mock_shuffle):
        mock_open.return_value = MagicMock(spec=file)
        self.fls.create_sftp_batch_files(["file_path1", "file_path2"], "pm_dir", "/tmp/pm_nbi_batch_{:02d}",
                                         num_of_sftp_batch_files=2, shuffle_data=False)
        self.assertFalse(mock_shuffle.called)

    def test_get_files(self):
        response = Mock()
        response.json.return_value = {"files": [{"id": None, "fileCreationTimeInOss": "time", "nodeName": "node_name1",
                                                 "fileLocation": "filename_blah1"}]}
        self.user.get.return_value = response
        self.assertTrue(self.fls.get_files("PM_STATISTICAL", "Radionode", 0, None))

    def test_get_files_with_topology_data_type(self):
        response = Mock()
        response.json.return_value = {"files": [{"id": 2, "fileCreationTimeInOss": "time", "nodeName": "node_name1",
                                                 "fileLocation": "filename_blah1"}]}
        self.user.get.return_value = response
        self.assertTrue(self.fls.get_files("TOPOLOGY", "Radionode", None, None))

    def test_get_files_with_non_topology_data_type(self):
        response = Mock()
        response.json.return_value = {"files": [{"id": 2, "fileCreationTimeInOss": "time", "nodeName": "node_name1",
                                                 "fileLocation": "filename_blah1"}]}
        self.user.get.return_value = response
        self.assertTrue(self.fls.get_files("PM_STATISTICAL", "Radionode", None, None))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
