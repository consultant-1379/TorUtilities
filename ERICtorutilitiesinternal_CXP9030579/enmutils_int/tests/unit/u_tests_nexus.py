#!/usr/bin/env python
import unittest2

from mock import patch, Mock, call, mock_open

from enmutils.lib import http
from enmutils_int.lib import nexus
from testslib import unit_test_utils

MOCK_PACKAGE_METADATA = """<metadata>
  <groupId>com.ericsson.dms.torutility</groupId>
  <artifactId>ERICtorutilities_CXP9030570</artifactId>
  <versioning>
    <latest>4.2.38</latest>
    <release>4.16.38</release>
    <versions>
      <version>1.0.1</version>
      <version>1.1.74</version>
      <version>1.8.19</version>
      <version>2.3.4</version>
      <version>4.3.25</version>
      <version>4.10.3</version>
      <version>4.16.38</version>
    </versions>
    <lastUpdated>20150820182642</lastUpdated>
  </versioning>
</metadata>"""


class NexusUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.nexus.http.get")
    def test_check_nexus_version_raises_connection_error(self, mock_http_get):
        mock_http_get.side_effect = http.requests.exceptions.ConnectionError("bad")
        version = nexus.check_nexus_version("none")
        self.assertFalse(version)

    @patch("enmutils_int.lib.nexus.http.get")
    def test_check_nexus_version_with_no_version_number_gets_latest_release(self, mock_http_get):
        response = Mock()
        response.rc = True
        response.content = MOCK_PACKAGE_METADATA
        mock_http_get.return_value = response
        self.assertEqual("4.16.38", nexus.check_nexus_version("prod", None))

    @patch("enmutils_int.lib.nexus.http.get")
    def test_check_nexus_version_with_suplied_version_number_bad(self, mock_http_get):
        response = Mock()
        response.rc = True
        response.content = MOCK_PACKAGE_METADATA
        mock_http_get.return_value = response
        version = nexus.check_nexus_version("prod", "6.6.6")
        self.assertFalse(version)

    @patch("enmutils_int.lib.nexus.http.get")
    def test_check_nexus_version_with_suplied_version_number_good(self, mock_http_get):
        response = Mock()
        response.rc = True
        response.content = MOCK_PACKAGE_METADATA
        mock_http_get.return_value = response
        version = nexus.check_nexus_version("prod", "1.0.1")
        self.assertEqual("1.0.1", version)

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", reutun_value=True)
    @patch("enmutils_int.lib.nexus.NEXUS_PROXY", {'https': 'some_url'})
    @patch("enmutils_int.lib.nexus._delete_old_artifacts")
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("enmutils_int.lib.nexus.os.path.join")
    @patch("enmutils_int.lib.nexus.http.get")
    @patch("enmutils_int.lib.nexus.os.path.isfile")
    def test_download_artifact_from_nexus__successfully_saves_to_file(
            self, mock_isfile, mock_http_get, mock_join, mock_open_file, *_):
        mock_file = "/tmp/enmutils/artifact-version.extension"
        mock_join.return_value = mock_file
        mock_isfile.side_effect = [False, True]
        response = Mock(ok=True, iter_content=lambda: ["some_content"])
        mock_http_get.return_value = response
        file_result = nexus.download_artifact_from_nexus("group", "artifact", "version", "extension")
        self.assertEqual(mock_file, file_result)
        self.assertTrue(call(mock_file) in mock_isfile.mock_calls)
        self.assertTrue(mock_open_file.called)
        download_url = ("https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?"
                        "r=releases&g=group&a=artifact&e=extension&v=version")
        mock_http_get.assert_called_with(download_url, proxies={'https': 'some_url'},
                                         verify=False, verbose=False)

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", reutun_value=False)
    @patch("enmutils_int.lib.nexus.NEXUS_PROXY", {'https': 'some_url'})
    @patch("enmutils_int.lib.nexus._delete_old_artifacts")
    @patch("__builtin__.open", new_callable=mock_open)
    @patch("enmutils_int.lib.nexus.os.path.join")
    @patch("enmutils_int.lib.nexus.http.get")
    @patch("enmutils_int.lib.nexus.os.path.isfile")
    def test_download_artifact_from_nexus__file_not_saved(self, mock_isfile, mock_get, *_):
        mock_isfile.return_value = False
        mock_get.return_value = Mock(ok=False, iter_content=lambda: ["some_content"])
        file_result = nexus.download_artifact_from_nexus("group", "artifact", "version", "extension")
        self.assertFalse(file_result)

    @patch("enmutils_int.lib.configure_wlvm_operations.check_deployment_to_disable_proxy", reutun_value=True)
    @patch("enmutils_int.lib.nexus.os.path.join")
    @patch("enmutils_int.lib.nexus.http.get")
    @patch("enmutils_int.lib.nexus.os.path.isfile")
    def test_download_artifact_from_nexus__file_already_exists(self, mock_isfile, mock_get, mock_join, *_):
        mock_isfile.return_value = True
        self.assertEqual(mock_join.return_value,
                         nexus.download_artifact_from_nexus("group", "artifact", "version", "extension"))
        self.assertFalse(mock_get.called)

    def test_latest_sprint_rpm(self):
        latest_sprint_rpm = nexus.get_released_rpm_version_per_sprint('latest')
        all_sprints_dict = nexus.get_released_rpm_version_per_sprint('all')
        self.assertTrue(all([latest_sprint_rpm and all_sprints_dict,
                             nexus.get_released_rpm_version_per_sprint('16.14') == '4.37.33',
                             nexus.get_released_rpm_version_per_sprint('latest') == latest_sprint_rpm,
                             nexus.get_released_rpm_version_per_sprint('all').get('16.15') == '4.38.8',
                             nexus.get_released_rpm_version_per_sprint('17.3') == '4.43.8',
                             nexus.get_released_rpm_version_per_sprint(nexus._get_sprint()) ==
                             nexus.get_prev_sprint_relased_version()]))

    @patch("enmutils_int.lib.nexus.does_file_exist", side_effect=[False, True])
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.nexus.http.get")
    def test_download_mavendata_from_nexus__is_successful_if_local_file_does_not_exists(self, *_):
        self.assertEqual("/tmp/enmutils/maven-metadata.xml", nexus.download_mavendata_from_nexus())

    @patch("enmutils_int.lib.nexus.delete_file")
    @patch("enmutils_int.lib.nexus.does_file_exist", return_value=True)
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.nexus.http.get")
    def test_download_mavendata_from_nexus__is_successful_if_local_file_exists(self, mock_get, *_):
        mock_get.return_value.iter_content.return_value = [Mock()]
        self.assertEqual("/tmp/enmutils/maven-metadata.xml", nexus.download_mavendata_from_nexus())

    @patch("enmutils_int.lib.nexus.delete_file")
    @patch("enmutils_int.lib.nexus.does_file_exist", return_value=False)
    @patch("__builtin__.open")
    @patch("enmutils_int.lib.nexus.http.get", return_value=Mock(ok=0))
    def test_download_mavendata_from_nexus__returns_false_if_cant_fetch_file(self, *_):
        self.assertFalse(nexus.download_mavendata_from_nexus())

    @patch("enmutils_int.lib.nexus.time.time", return_value=8 * 86400)
    @patch("enmutils_int.lib.nexus.os.listdir", return_value=["abc", "abc", "bcd"])
    @patch("enmutils_int.lib.nexus.os.path.join", return_value="nexus_path")
    @patch("enmutils_int.lib.nexus.os.stat", return_value=Mock(st_mtime=0))
    @patch("enmutils_int.lib.nexus.os.remove")
    @patch("enmutils_int.lib.nexus.log.logger.debug")
    def test_delete_old_articrafts__remove_file_path_when_file_not_modified(self, mock_log, mock_remove, *_):
        nexus._delete_old_artifacts("abc")
        self.assertEqual(mock_log.call_count, 2)
        mock_remove.assert_called_with("nexus_path")

    @patch("enmutils_int.lib.nexus.time.time", return_value=8 * 86400)
    @patch("enmutils_int.lib.nexus.os.listdir", return_value=["abc", "abc", "bcd"])
    @patch("enmutils_int.lib.nexus.os.path.join", return_value="nexus_path")
    @patch("enmutils_int.lib.nexus.os.stat", return_value=Mock(st_mtime=2 * 86400))
    @patch("enmutils_int.lib.nexus.os.remove")
    @patch("enmutils_int.lib.nexus.log.logger.debug")
    def test_delete_old_articrafts__when_file_is_modified(self, mock_log, mock_remove, *_):
        nexus._delete_old_artifacts("abc")
        self.assertEqual(mock_log.call_count, 0)

    @patch("enmutils_int.lib.nexus.Command")
    @patch("enmutils_int.lib.nexus.run_local_cmd")
    def test_get_sprint__success(self, mock_local_cmd, _):
        mock_local_cmd.return_value = Mock(ok=True, stdout="ENM 12.34")
        self.assertEqual("12.33", nexus._get_sprint())

    @patch("enmutils_int.lib.nexus.Command")
    @patch("enmutils_int.lib.nexus.run_local_cmd")
    def test_get_sprint__returns_previous_when_response_not_ok(self, mock_local_cmd, _):
        mock_local_cmd.return_value = Mock(ok=False, stdout="ENM 12.34")
        self.assertEqual("previous", nexus._get_sprint())

    @patch("enmutils_int.lib.nexus.re.findall", return_value=" ")
    @patch("enmutils_int.lib.nexus.Command")
    @patch("enmutils_int.lib.nexus.run_local_cmd")
    def test_get_sprint__with_no_sprint(self, mock_local_cmd, *_):
        mock_local_cmd.return_value = Mock(ok=True, stdout="ENM")
        self.assertEqual("", nexus._get_sprint())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
